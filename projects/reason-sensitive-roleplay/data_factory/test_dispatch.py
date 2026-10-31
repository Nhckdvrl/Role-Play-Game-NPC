import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import agent_dispatch

SCHEMA = {'type': 'object', 'properties': {'answer': {'type': 'integer'}},
          'required': ['answer'], 'additionalProperties': False}
TASK = {'stage': 'test', 'payload': {'input': 'x'}, 'instruction': 'Respond.', 'output_schema': SCHEMA}
EVENTS = b'{"type":"thread.started","thread_id":"t1"}\n{"type":"turn.completed","usage":{"input_tokens":3}}\n'


class FakeProcess:
    def __init__(self, argv, *, body=b'{"answer":1}', events=EVENTS, timeout=False, **kwargs):
        self.argv, self.body, self.events, self.timeout = argv, body, events, timeout
        self.pid = 12345
        self.returncode = None
        self.calls = 0

    def communicate(self, input=None, timeout=None):
        self.calls += 1
        if self.timeout and self.calls == 1:
            raise subprocess.TimeoutExpired(self.argv, timeout, output=b'partial')
        if not self.timeout:
            Path(self.argv[self.argv.index('-o') + 1]).write_bytes(self.body)
            self.returncode = 0
            return self.events, b''
        self.returncode = -9
        return b'partial', b'partial error'


class DispatchTest(unittest.TestCase):
    def run_fake(self, **kwargs):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        calls = []
        def make(argv, **options):
            proc = FakeProcess(argv, **kwargs, **options)
            calls.append(proc)
            return proc
        return tmp.name, calls, patch.object(agent_dispatch.subprocess, 'Popen', side_effect=make)

    def test_schema_error_is_failed_and_preserves_raw(self):
        path, calls, popen = self.run_fake(body=b'{"answer":"not an integer"}')
        with popen:
            result = agent_dispatch.dispatch(TASK, path)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(len(calls), 3)
        attempt = Path(result['path'])
        meta = json.loads((attempt / 'metadata.json').read_text())
        self.assertEqual(meta['failure_type'], 'schema_validation_error')
        self.assertEqual((attempt / 'raw.last.txt').read_text(), '{"answer":"not an integer"}')
        self.assertIn('prompt_sha256', meta)
        self.assertIn('payload_sha256', meta)

    def test_tool_event_rejected_even_with_valid_result(self):
        tool = b'{"type":"item.completed","item":{"type":"command_execution"}}\n'
        path, calls, popen = self.run_fake(events=tool + EVENTS)
        with popen:
            result = agent_dispatch.dispatch(TASK, path)
        meta = json.loads((Path(result['path']) / 'metadata.json').read_text())
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(meta['failure_type'], 'forbidden_tool')
        self.assertIn('command_execution', meta['forbidden_events'])

    def test_timeout_kills_group_and_keeps_partial_output(self):
        path, calls, popen = self.run_fake(timeout=True)
        with popen, patch.object(agent_dispatch.os, 'killpg') as kill:
            result = agent_dispatch.dispatch(TASK, path, timeout=1)
        attempt = Path(result['path'])
        meta = json.loads((attempt / 'metadata.json').read_text())
        self.assertEqual(meta['failure_type'], 'timeout')
        self.assertEqual((attempt / 'events.jsonl').read_text(), 'partial')
        self.assertEqual((attempt / 'stderr.txt').read_text(), 'partial error')
        self.assertEqual(kill.call_count, 3)

    def test_success_is_cached_without_second_process(self):
        path, calls, popen = self.run_fake()
        with popen:
            first = agent_dispatch.dispatch(TASK, path)
            second = agent_dispatch.dispatch(TASK, path)
        self.assertEqual(first['result'], {'answer': 1})
        self.assertTrue(second['reused'])
        self.assertEqual(len(calls), 1)
        meta = json.loads((Path(first['path']) / 'metadata.json').read_text())
        self.assertEqual(meta['usage']['input_tokens'], 3)
        self.assertEqual(meta['thread_id'], 't1')


if __name__ == '__main__':
    unittest.main()
