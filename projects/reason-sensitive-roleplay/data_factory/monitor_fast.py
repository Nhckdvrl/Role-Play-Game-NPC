"""Report completed production and metered CLI usage without writing dataset labels."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
import subprocess
import time

from fast_generate import atomic, put
from quality import analyze


def read(path, default=None):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def checkpoint(run, project, count):
    threshold = count // 250 * 250
    if not threshold:
        return
    output = run / 'checkpoints' / f'{threshold:06d}'
    if (output / 'snapshot.json').exists():
        return
    content = (run / 'families.jsonl').read_bytes()
    families = [json.loads(line) for line in content.decode().splitlines() if line.strip()]
    pilot = project / 'runs/pilot12-20261101-semantic-v4/families.jsonl'
    comparison = [json.loads(line) for line in pilot.read_text().splitlines() if line.strip()] if pilot.exists() else []
    output.mkdir(parents=True, exist_ok=True)
    atomic(output / 'families.jsonl', content.decode())
    quality = analyze(families, comparison)
    put(output / 'quality.json', quality)
    put(output / 'snapshot.json', {
        'utc': datetime.now(timezone.utc).isoformat(), 'trigger_threshold': threshold,
        'source': str(run / 'families.jsonl'), 'sha256': hashlib.sha256(content).hexdigest(),
        'actual_families': len(families), 'nodes': len(families) * 12,
        'candidate_instances': sum(len(b['candidates']) for f in families for b in f['branches']),
        'history_modes': dict(Counter(f['history_mode'] for f in families)),
        'human_review': 'not_sampled', 'quality_scope': 'mechanical; independent semantic records remain in source runs',
    })
    interpreter = Path('/home/xiang/.venvs/data-centric-rsi/bin/python')
    tokenizer = Path('/home/xiang/.cache/huggingface/hub/models--microsoft--Phi-4-mini-instruct/snapshots/cfbefacb99257ffa30c83adab238a50856ac3083')
    if interpreter.exists() and tokenizer.exists():
        argv = [str(interpreter), str(project / 'data_factory/measure_histories.py'),
                str(output / 'families.jsonl'), '--out', str(output / 'token_measurements.json'),
                '--tokenizer', str(tokenizer)]
        with (output / 'token_measurements.log').open('a') as log:
            process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=log,
                                       stderr=log, start_new_session=True)
        put(output / 'token_measurement_launch.json', {'argv': argv, 'pid': process.pid,
                                                      'status': 'started_not_yet_verified'})


def once(run, project, usage_cache):
    state = read(run / 'state.json', {})
    launch = read(run / 'launch.json', {})
    pid_path = run / 'production.pid'
    pid = int(pid_path.read_text()) if pid_path.exists() else None
    alive = pid is not None and Path(f'/proc/{pid}').exists()
    native = read(project / 'runs/NATIVE_PRODUCTION.json', {})
    completed = state.get('completed', [])
    counts = Counter(row['status'] for row in completed)
    utc = datetime.now(timezone.utc).isoformat()
    scope = ['train5000-live', 'fast-stream-v21', 'fast-stream-v2', 'fast-stream-main', 'fast-stream-probe',
             'fast-lane-20261101', 'fast-lane-wave2', 'field-natural-20261101',
             'fast-astra-spot-20261101', 'global-quality-live']
    for name in scope:
        for path in (project / 'runs' / name).rglob('metadata.json'):
            if str(path) not in usage_cache:
                row = read(path)
                if row:
                    usage_cache[str(path)] = row
    usage = Counter()
    missing = 0
    for row in usage_cache.values():
        if row.get('usage') is None:
            missing += 1
        else:
            usage.update({k: v for k, v in row['usage'].items()
                          if isinstance(v, (int, float))})
    report = {
        'utc': utc, 'run': str(run), 'pid': pid, 'process_alive': alive,
        'target_train_families': 5000, 'audited_train': state.get('audited_train', 0),
        'candidate_instances': state.get('candidate_instances', 0),
        'unique_candidate_texts_global': state.get('unique_candidate_texts_global', 0),
        'concurrency': launch.get('concurrency'), 'completed_new_jobs': dict(counts),
        'quota_blocked': state.get('quota_blocked', False),
        'native_production': native,
        'stop_reason': state.get('stop_reason'),
        'imported_v2_families': len(state.get('imports', {})),
        'quality_scheduler': state.get('quality_scheduler'),
        'edge_recovery_stats': state.get('edge_recovery_stats'),
        'historical_mechanical_failures': len(state.get('edge_recovery_history', [])),
        'current_run_completed_generation_json': sum(1 for _ in (run / 'jobs').glob('*/raw_compact.json')),
        'human_review': 'not_sampled',
        'usage': {'scope_runs': scope, 'completed_cli_metadata': len(usage_cache),
                  'returned_usage': dict(usage), 'missing_usage': missing,
                  'cost_usd': None,
                  'exclusions': 'native subagent sessions, unfinished CLI calls, old calibration runs'},
    }
    put(run / 'live_report.json', report)
    checkpoint(run, project, report['audited_train'])
    with (run / 'observations.jsonl').open('a') as handle:
        handle.write(json.dumps({k: v for k, v in report.items() if k != 'usage'},
                                ensure_ascii=False) + '\n')
    start, end = '<!-- TRAIN_LIVE_START -->', '<!-- TRAIN_LIVE_END -->'
    progress = project / 'DATA_PROGRESS.md'
    original = progress.read_text()
    if start in original and end in original:
        scheduler = state.get('quality_scheduler') or {}
        rate = scheduler.get('rate')
        if rate is None and completed:
            rate = counts['audited'] / len(completed)
        text = (f'\n\n更新：{utc}。当前累计 **{report["audited_train"]}/5000 个 Train 故事族**，'
                f'{report["candidate_instances"]} 个四格候选实例，'
                f'{report["unique_candidate_texts_global"]} 条全局唯一候选正文。\n\n'
                f'CLI 配置并发上限：{report["concurrency"]}；CLI 进程：'
                f'{"运行中" if alive else "已退出"}，额度阻断：{report["quota_blocked"]}。'
                f'原生生产：{native.get("status", "未记录")}，领队：{native.get("lead_task", "未记录")}。'
                f'已记录审查结果：{dict(counts)}；'
                f'最近调度窗通过率：{f"{rate:.1%}" if rate is not None else "等待首批完成"}。'
                f'排除和待审均不计入。停止原因：{report["stop_reason"] or "无"}。\n\n'
                f'数据与原始盲审：`runs/{run.name}/`；旧批匿名重审：'
                '`runs/fast-v2-migration/`；用量范围和缺失项见 '
                f'`runs/{run.name}/live_report.json`，费用尚无实测账单。\n\n')
        atomic(progress, original.split(start)[0] + start + text + end + original.split(end, 1)[1])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--interval', type=float, default=45)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    if args.interval < 5:
        parser.error('interval must be at least five seconds')
    project = Path(__file__).resolve().parent.parent
    run = args.run_dir.resolve()
    cache = {}
    while True:
        report = once(run, project, cache)
        print(json.dumps({k: v for k, v in report.items() if k != 'usage'},
                         ensure_ascii=False), flush=True)
        if args.once or (not report['process_alive'] and report['stop_reason'] == 'target reached'):
            break
        time.sleep(args.interval)


if __name__ == '__main__':
    main()
