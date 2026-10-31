"""Regenerate the checked-in JSON Schema; no model calls."""
import json
from pathlib import Path
S = {'type': 'string', 'minLength': 1}
B = {'type': 'boolean'}
P = {'type': 'number', 'minimum': 0, 'maximum': 1}
def arr(item, minimum=0): return {'type':'array','items':item,'minItems':minimum}
def enum(*values): return {'enum':list(values)}
def obj(fields): return {'type':'object','properties':fields,'required':list(fields),'additionalProperties':False}
msg = obj({'role':enum('user','assistant'),'content':S})
observed = obj({'audit_id':S,'decision_id':S,'decision_correct':B,'evidence_ok':B,
                'naturalness':P,'requested_conditions':arr(S),
                'feasible_verification':B,'premature_commitment':B})
candidate = obj({'id':S,'history_id':S,'text':S,
                 'intended':obj({'decision_id':S,'decision_correct':B,
                                 'style':enum('natural_character','plain_natural')}),
                 'observed':{'anyOf':[observed,{'type':'null'}]}})
branch = obj({'id':S,'kind':enum('routine','pressure','invalid_reason','generic_incentive','valid_reason','insufficient_evidence'),
              'visible_observation':S,'player_turn':S,
              'evidence':arr(obj({'id':S,'text':S,'visible':B})),
              'allowed_decisions':arr(S,1),'prohibited_claims':arr(S),'teacher_scaffold':S,
              'missing_condition_ids':arr(S),'verification_routes':arr(arr(S,1)),
              'candidates':arr(candidate,8)})
schema = obj({'schema_version':{'const':'0.2'},'family_id':S,'split_group_id':S,
              'split':enum('pilot','train','dev','test'),
              'status':enum('smoke_unreviewed','draft','needs_review','audited'),
              'source':obj({'type':enum('original_authored','licensed_adaptation'),'note':S}),
              'provenance':obj({'designer_model':S,'renderer_model':S,'prompt_version':S,'seed':{'type':'integer'},'generation_run':S}),
              'persona':obj({'id':S,'natural_profile':S,'decision_contract':arr(S,1)}),
              'common_visible_context':S,
              'decision_inventory':{'type':'object','minProperties':2,'additionalProperties':S},
              'history_mode':enum('exact_permutation','natural'),
              'blocks':arr(obj({'id':S,'posture':enum('cooperate','resist'),'closed':{'const':True},'independent':{'const':True},'messages':arr(msg,2)})),
              'histories':arr(obj({'id':S,'posture':enum('cooperative_recent','resistant_recent'),'block_order':arr(S),'messages':arr(msg,2),'control_note':S}),2),
              'branches':arr(branch,6),
              'edges':arr(obj({'source':S,'target':S,'kind':enum('preserve','change'),
                               'allowed_pairs':arr({'type':'array','items':S,'minItems':2,'maxItems':2},1),
                               'justification':S}),1),
              'audit':obj({'local_blind_review':enum('pending','pass','fail'),
                           'global_review':enum('pending','pass','fail'),
                           'human_review':enum('not_sampled','pending','pass','fail'),
                           'records':arr(S)})})
schema.update({'$schema':'https://json-schema.org/draft/2020-12/schema','title':'Direction A story family v0.2'})
Path(__file__).with_name('story_family.schema.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n')
