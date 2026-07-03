import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import Gen  # noqa: E402


class LoadRegexesTests(unittest.TestCase):
    def test_load_text_regexes_skips_blank_lines(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset = Path(tmpdir) / "regexes.txt"
            dataset.write_text("^(a+)+$\n\n([a-z]+)*$\n", encoding="utf-8")

            regexes = Gen.load_regexes(str(dataset))

        self.assertEqual(
            regexes,
            [
                {
                    "id": 1,
                    "source_line": 1,
                    "regex": "^(a+)+$",
                    "base64regex": "XihhKykrJA==",
                },
                {
                    "id": 3,
                    "source_line": 3,
                    "regex": "([a-z]+)*$",
                    "base64regex": "KFthLXpdKykqJA==",
                },
            ],
        )

    def test_load_ndjson_regexes_preserves_multiline_and_nul_patterns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset = Path(tmpdir) / "production.ndjson"
            rows = [
                {"pattern": ""},
                {"pattern": "\n\t "},
                {"pattern": "\ufeff"},
                {"pattern": "foo\nbar"},
                {"pattern": "A\u0000B"},
                {"pattern": "x\ud800y"},
                {"pattern": False},
            ]
            dataset.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

            with mock.patch.object(Gen, "print_status") as print_status:
                regexes = Gen.load_regexes(str(dataset))

        self.assertEqual([row["id"] for row in regexes], [4, 5])
        self.assertEqual([row["regex"] for row in regexes], ["foo\nbar", "A\x00B"])
        self.assertEqual(regexes[0]["base64regex"], "Zm9vCmJhcg==")
        self.assertEqual(regexes[1]["base64regex"], "QQBC")
        self.assertEqual(
            [call.args[0] for call in print_status.call_args_list],
            [
                "[Gen] skipped 1 NDJSON records whose pattern field was not a string",
                "[Gen] skipped 1 NDJSON records whose pattern field was an empty string",
                "[Gen] skipped 1 NDJSON records whose pattern field contained only whitespace",
                "[Gen] skipped 1 NDJSON records whose pattern field would become empty after JavaScript trim()",
                "[Gen] skipped 1 NDJSON records whose pattern field contained UTF-16 surrogate code points",
            ],
        )


if __name__ == "__main__":
    unittest.main()
