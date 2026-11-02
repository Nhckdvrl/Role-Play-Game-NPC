"""CoSER Given-Circumstance Acting (GCA) evaluation (Wang et al., ICML 2025), re-implemented from the official
gca_evaluation/main.py + agent.py after review; prompt text verbatim in coser_prompts.py.

Per test scene: the actor (policy under test) plays every speaking character, each with its own CoSER character prompt
(+ the agent's "Speak concisely ... 60 words" suffix); an environment agent and a next-speaker predictor (NSP) drive
turn-taking for up to 20 rounds; each agent sees others' messages with inner thoughts removed. A critic then lists flaws
per dimension (Storyline Consistency, Anthropomorphism, Character Fidelity, Storyline Quality) against the original
book dialogue; score = max(0, min(100 - (sum severity - 0.3 * actor_rounds) * 5, 100)).
Differences from the official run: environment / NSP / critic = Qwen3-32B instead of GPT-4o(-mini) (absolute scores are
not comparable with the paper; paired model comparisons are); no repetition post-fix for the actor; no LLM JSON repair
(failed parses are retried at temperature 1, up to 5 times, as in get_response_json); scenes run in parallel.
"""
import json, argparse, os, sys, random, copy
from concurrent.futures import ThreadPoolExecutor
import openai
sys.path.insert(0, os.path.dirname(__file__))
import coser_prompts as C

ap = argparse.ArgumentParser()
ap.add_argument("--test_file", default="/home/xiang/rp_persona/src/coser/data/test/test_set.json")
ap.add_argument("--actor", required=True, help="served model name of the policy")
ap.add_argument("--routes", required=True, help='JSON {"model_name": "http://host:port/v1", ...}')
ap.add_argument("--aux_model", default="q32", help="environment / NSP / critic model")
ap.add_argument("--outdir", default="/home/xiang/rp_persona/runs/coser")
ap.add_argument("--workers", type=int, default=48)
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--stage", default="sim,judge")
args = ap.parse_args()

ENV, NSP = "Environment", "NSP"
ROUTES = json.loads(args.routes)
CLIENTS = {m: openai.OpenAI(api_key="EMPTY", base_url=u, timeout=900) for m, u in ROUTES.items()}


def get_response(model, messages, max_tokens=None, nth_generation=0):
    merged = []
    for m in messages:                                   # merge adjacent user messages (as CoSER's get_response)
        if m["role"] == "user" and merged and merged[-1]["role"] == "user":
            merged[-1]["content"] += m["content"]
        else:
            merged.append(copy.deepcopy(m))
    for attempt in range(3):
        try:
            c = CLIENTS[model].chat.completions.create(model=model, messages=merged, max_tokens=max_tokens or 4096,
                                                       temperature=0 if nth_generation == 0 else 1,
                                                       extra_body={"chat_template_kwargs": {"enable_thinking": False}})
            return c.choices[0].message.content or ""
        except Exception as e:
            err = e
    print(f"get_response failed ({model}): {err}", flush=True)
    return None


def get_response_json(post, model, messages, max_tokens=None, max_retry=5):
    n = 0
    while True:
        r = get_response(model, messages, max_tokens, nth_generation=n)
        for f in post:
            r = f(r) if r is not None else None
        if r:
            return r
        n += 1
        if n > max_retry:
            return r


class Agent:
    def __init__(self, model, name, system_prompt):
        self.model, self.name = model, name
        sp = system_prompt.strip("\n")
        if name not in (ENV, NSP):
            sp += "\n\nSpeak concisely as humans, instead of being verbose. Limit your response to 60 words.\n\n"
        self.messages = [{"role": "system", "content": sp}]

    def chat(self):
        return get_response_json([], self.model, self.messages, max_tokens=512) or ""

    def update(self, role, message):
        if message:
            if self.messages and self.messages[-1]["role"] == role:
                self.messages[-1]["content"] += "\n\n" + message
            else:
                self.messages.append({"role": role, "content": message})


def simulate(idx, circ):
    rng = random.Random(42 + idx)
    plot, conv = circ["plot"], circ
    plot_chars = [c["name"] for c in plot["key_characters"]]
    speaking = list(conv["speaking_characters_w_env"])
    if ENV not in speaking:
        speaking.append(ENV)
    major = conv["major_characters"]
    profiles = {}
    for ch in speaking:
        if ch == ENV:
            continue
        prof = circ["character_profiles"].get(ch, "")
        if ch in plot_chars:
            info = [c for c in plot["key_characters"] if c.get("name", "") == ch][0]
            if "description" in info:
                prof = info.get("description", "").strip("\n") + "\n\n" + prof.strip("\n")
        prof = prof.strip(" \n")
        if prof:
            profiles[ch] = prof
    agents = {}
    for ch in speaking + [NSP]:
        if ch == NSP:
            agents[ch] = Agent(args.aux_model, ch, C.get_nsp_prompt(speaking, conv["scenario"]))
        elif ch == ENV:
            agents[ch] = Agent(args.aux_model, ch, C.get_environment_prompt(major, conv["scenario"], rng))
        else:
            mot = [c.get("motivation", "") for c in conv["key_characters"] if c.get("name", "") == ch]
            agents[ch] = Agent(args.actor, ch, C.get_character_prompt(circ["book"], ch, profiles.get(ch, ""), conv["scenario"],
                                                                     mot[0] if mot else "", profiles, rng))
        agents[ch].update("user", "===Conversation Start===\n\n")
    log, cur = [], speaking[0]
    for i_round in range(20):
        if cur == "<END CHAT>":
            break
        for actor in [cur, NSP]:
            ag = agents[actor]
            resp = ag.chat()
            if actor == NSP:
                nxt = C.extract_nsp(resp)
                if nxt is None:
                    nxt = resp.split(":")[0].strip() if ":" in resp else resp
                invalid = False
                if nxt == "<END CHAT>" and i_round >= 5:
                    cur = "<END CHAT>"
                elif nxt in speaking and nxt != cur:
                    cur = nxt
                else:
                    invalid = True
                    cands = set(major + [ENV]) - {cur} or set(speaking) - {cur}
                    cur = rng.choice(sorted(cands))
                log.append({"role": actor, "content": nxt})
                if not invalid:
                    ag.update("assistant", resp)
                else:
                    ag.update("assistant", nxt)
                    ag.update("user", ag.messages[0]["content"])
            else:
                log.append({"role": actor, "content": resp})
                for other, oa in agents.items():
                    if other == actor:
                        oa.update("assistant", resp)
                    else:
                        oa.update("user", C.add_speaker_name(C.remove_inner_thoughts(resp), actor))
    return {"idx": idx, "book_title": circ["book"], "i_p": plot["i_p"], "i_c": conv["i_c"], "circumstance": circ,
            "simulation": log, "involved_character_profiles": profiles}


DIMS = ["Storyline Consistency", "Anthropomorphism", "Character Fidelity", "Storyline Quality"]


def judge(res):
    circ = res["circumstance"]
    sim = [m for m in res["simulation"] if m["role"] != NSP]
    ref = circ["dialogues"]
    sim = [m if m["role"] == ENV else {**m, "content": C.remove_inner_thoughts(m["content"])} for m in sim]
    ref = [m if m["character"] == ENV else {**m, "message": C.remove_inner_thoughts(m["message"])} for m in ref]
    sim_str = "\n\n".join([m["content"].strip("\n") for m in sim])
    ref_str = "\n\n".join([f"{m['character']}: {m['message']}".strip("\n") for m in ref])
    prof_str = "\n\n".join([f"### {c}\n\n{p.strip('')}" for c, p in res["involved_character_profiles"].items()])

    def parse(r):
        try:
            assert isinstance(r, dict)
            for k, v in r.items():
                assert k in DIMS and "flaws" in v
                for f in v["flaws"]:
                    if f.get("severity", None) is None:
                        f["severity"] = 1
            return r
        except Exception:
            return False

    rounds = len([m for m in sim if m["role"] != ENV])
    out = {}
    for d in DIMS:
        p = C.critic_prompts["self-play-deduct-template"].replace("{book}", res["book_title"]).replace("{plot_summary}", circ["plot"]["summary"]) \
            .replace("{scenario}", circ["scenario"]).replace("{character_profiles}", prof_str).replace("{original_conversation}", ref_str) \
            .replace("{major_characters}", ", ".join(circ["major_characters"])).replace("{additional_instructions}", "") \
            .replace("{dimension_name}", d).replace("{dimension_brief}", C.critic_prompts["dimension_details"][d]["dimension_brief"]) \
            .replace("{dimension_criteria}", C.critic_prompts["dimension_details"][d]["dimension_criteria"])
        r = get_response_json([C.extract_json, parse], args.aux_model, [{"role": "system", "content": p}, {"role": "user", "content": sim_str}])
        r = r.get(d, {"flaws": []}) if isinstance(r, dict) else {"flaws": [], "parse_failed": True}
        r["score"] = max(0, min(100 - (sum(f["severity"] for f in r["flaws"] if isinstance(f.get("severity"), int)) - 0.3 * rounds) * 5, 100))
        out[d] = r
    return {"idx": res["idx"], "key": f"{res['book_title']}-{res['i_p']}-{res['i_c']}", "book": res["book_title"],
            "scores": {d: out[d]["score"] for d in DIMS}, "actor_rounds": rounds, "critique": out}


os.makedirs(args.outdir, exist_ok=True)
test = json.load(open(args.test_file))
if args.limit:
    test = test[: args.limit]
sim_path, eval_path = f"{args.outdir}/sim_{args.actor}.json", f"{args.outdir}/eval_{args.actor}.json"
if "sim" in args.stage:
    with ThreadPoolExecutor(args.workers) as ex:
        sims = list(ex.map(lambda t: simulate(*t), enumerate(test)))
    json.dump(sims, open(sim_path, "w"), ensure_ascii=False)
    print("simulated", len(sims), flush=True)
if "judge" in args.stage:
    sims = json.load(open(sim_path))
    with ThreadPoolExecutor(args.workers) as ex:
        evs = list(ex.map(judge, sims))
    json.dump(evs, open(eval_path, "w"), ensure_ascii=False)
    avg = {d: sum(e["scores"][d] for e in evs) / len(evs) for d in DIMS}
    print(args.actor, {k: round(v, 2) for k, v in avg.items()}, "avg", round(sum(avg.values()) / 4, 2), flush=True)
