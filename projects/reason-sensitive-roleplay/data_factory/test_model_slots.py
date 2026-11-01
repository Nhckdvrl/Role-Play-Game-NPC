import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import agent_dispatch


class ModelSlotTests(unittest.TestCase):
    def test_eight_shared_slots_across_processes(self):
        worker = '''import json,os,sys,time\nfrom pathlib import Path\nimport agent_dispatch as a\na.MODEL_SLOT_DIR=Path(sys.argv[1])/'slots'\np=Path(sys.argv[1])/'events.jsonl'\ndef emit(t):\n fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600);os.write(fd,(json.dumps({'event':t,'pid':os.getpid()})+'\\n').encode());os.close(fd)\nwith a._model_slot():\n emit('start');time.sleep(.3);emit('end')\n'''
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, PYTHONPATH=str(Path(agent_dispatch.__file__).parent))
            procs = [subprocess.Popen([sys.executable, '-c', worker, d], env=env) for _ in range(12)]
            for p in procs:
                self.assertEqual(0, p.wait(timeout=20))
            events = [json.loads(line) for line in (Path(d)/'events.jsonl').read_text().splitlines()]
            active = peak = 0
            for event in events:
                active += 1 if event['event'] == 'start' else -1
                peak = max(peak, active)
                self.assertLessEqual(active, 8)
                self.assertGreaterEqual(active, 0)
            self.assertEqual(0, active)
            self.assertEqual(8, peak)

    def test_slot_released_when_body_raises(self):
        with tempfile.TemporaryDirectory() as d, patch.object(agent_dispatch, 'MODEL_SLOT_DIR', Path(d)):
            with self.assertRaisesRegex(RuntimeError, 'failure'):
                with agent_dispatch._model_slot():
                    raise RuntimeError('failure')
            with agent_dispatch._model_slot():
                pass


if __name__ == '__main__':
    unittest.main()
