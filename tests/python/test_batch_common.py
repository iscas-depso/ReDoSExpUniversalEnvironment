import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import batch_common  # noqa: E402


class ParseBackendJsonOutputTests(unittest.TestCase):
    def test_parses_json_with_unicode_line_separator_chars_inside_string(self):
        payload = {
            "status": "completed",
            "metadata": {
                "payloadPreview": "prefix\u0085suffix"
            }
        }
        stdout_text = json.dumps(payload, ensure_ascii=False)

        parsed = batch_common.parse_backend_json_output(stdout_text)

        self.assertEqual(parsed, payload)

    def test_falls_back_to_last_complete_json_object(self):
        payload = {"status": "completed", "value": 7}
        stdout_text = "engine debug banner\\n" + json.dumps(payload)

        parsed = batch_common.parse_backend_json_output(stdout_text)

        self.assertEqual(parsed, payload)


class RunBackendTests(unittest.TestCase):
    @mock.patch("batch_common.subprocess.run")
    def test_run_backend_handles_unicode_separator_output(self, run_mock):
        payload = {
            "status": "completed",
            "metadata": {
                "payloadPreview": "A\u0085B"
            }
        }
        run_mock.return_value = subprocess.CompletedProcess(
            args=["node", "scripts/batch-backend.js", "run-engine"],
            returncode=0,
            stdout=json.dumps(payload, ensure_ascii=False),
            stderr=""
        )

        result = batch_common.run_backend("run-engine", {"demo": True})

        self.assertEqual(result, payload)


if __name__ == "__main__":
    unittest.main()
