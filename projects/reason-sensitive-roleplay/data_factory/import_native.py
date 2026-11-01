"""Canonicalize audit references and import reviewed native data without model calls."""
import argparse
from copy import deepcopy
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from fast_generate import atomic, put
from factory import validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, action='append', required=True)
    args = parser.parse_args()
    project = Path(__file__).resolve().parent.parent
    repository = project.parent.parent
    output = project / 'runs/native-import'
    output.mkdir(parents=True, exist_ok=True)
    families, changes = {}, []
    for source in args.source:
        for line in source.read_text().splitlines():
            if not line.strip():
                continue
            original = json.loads(line)
            validate(original)
            if original['status'] != 'audited' or original['split'] != 'train':
                raise ValueError('Only independently audited Train families may be imported')
            family = deepcopy(original)
            references = []

            def canonical(reference):
                path, separator, fragment = reference.partition('#')
                path = Path(path)
                choices = [path] if path.is_absolute() else [project / path, repository / path]
                matches = {p.resolve() for p in choices if p.is_file()}
                if len(matches) != 1:
                    raise ValueError(f'Missing or ambiguous audit path: {reference}')
                normalized = str(matches.pop()) + (separator + fragment if separator else '')
                if normalized != reference:
                    references.append({'before': reference, 'after': normalized})
                return normalized

            family['audit']['records'] = [canonical(r) for r in family['audit']['records']]
            for branch in family['branches']:
                for candidate in branch['candidates']:
                    candidate['observed']['audit_id'] = canonical(candidate['observed']['audit_id'])
            fid = family['family_id']
            if fid in families and families[fid] != family:
                raise ValueError(f'Conflicting imported family: {fid}')
            families[fid] = family
            changes.append({'family_id': fid, 'source': str(source.resolve()),
                            'source_row_sha256': hashlib.sha256(line.encode()).hexdigest(),
                            'reference_changes_only': references})
    atomic(output / 'passed.jsonl', ''.join(json.dumps(f, ensure_ascii=False) + '\n'
                                          for f in families.values()))
    put(output / 'reference_normalization.json', changes)
    # The live controller consumes this file on every save; do not launch a
    # second controller merely to import into an already locked run directory.
    run = project / 'runs/train5000-live'
    with (run / '.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            argv = json.loads((run / 'launch.json').read_text())['argv']
            imports = [Path(argv[i+1]) for i, item in enumerate(argv[:-1]) if item == '--import-snapshot']
            imports = [(path if path.is_absolute() else project/path).resolve() for path in imports]
            if (output/'passed.jsonl').resolve() not in imports:
                raise RuntimeError('active controller does not consume the prepared import file')
            print(json.dumps({'status': 'prepared_for_active_controller', 'families': len(families), 'model_calls': 0}))
            return
    subprocess.run([sys.executable, str(project / 'data_factory/fast_generate.py'),
                    '--run-dir', str(project / 'runs/train5000-live'), '--target', '5000',
                    '--concurrency', '8', '--import-snapshot', str(output / 'passed.jsonl'),
                    '--import-only'], cwd=project, check=True)


if __name__ == '__main__':
    main()
