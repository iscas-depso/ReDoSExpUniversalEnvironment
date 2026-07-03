import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import Gen  # noqa: E402


class ResumeImportTests(unittest.TestCase):
    def make_regexes(self):
        return [
            {"id": 1, "source_line": 1, "regex": "a", "base64regex": "YQ=="},
            {"id": 2, "source_line": 2, "regex": "b", "base64regex": "Yg=="},
            {"id": 4, "source_line": 4, "regex": "d", "base64regex": "ZA=="},
        ]

    def test_imports_only_trustworthy_rows_for_current_regex_set(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target_db = Path(tmpdir) / "target.db"
            source_db = Path(tmpdir) / "source.db"

            Gen.setup_database(str(target_db))
            Gen.insert_regexes(str(target_db), self.make_regexes())

            Gen.setup_database(str(source_db))
            source_regexes = self.make_regexes() + [
                {"id": 3, "source_line": 3, "regex": "c", "base64regex": "Yw=="},
                {"id": 5, "source_line": 5, "regex": "e", "base64regex": "ZQ=="},
            ]
            Gen.insert_regexes(str(source_db), source_regexes)

            conn = sqlite3.connect(source_db)
            try:
                conn.execute(
                    """
                    INSERT INTO attack_result
                    (tool, id, status, is_redos, elapsed_ms, time, time_source, walltime_ms, cputime_ms, memory_bytes, error_type)
                    VALUES
                    ('grewia', 1, 'completed', 1, 11, 11, 'tool', 12, 10, 4096, NULL),
                    ('grewia', 2, 'failed', 0, 7, NULL, NULL, NULL, NULL, NULL, 'tool_exception'),
                    ('grewia', 3, 'completed', 1, 9, 9, 'tool', 10, 8, 2048, NULL),
                    ('grewia', 4, 'completed', 1, 13, 13, 'tool', 14, 12, NULL, NULL),
                    ('grewia', 5, 'inconclusive', 0, 5, NULL, NULL, NULL, NULL, NULL, 'infra_error')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO attack_candidate
                    (tool, id, candidate_id, candidate_label, is_recommended, attack_type, full_text)
                    VALUES
                    ('grewia', 1, 'candidate-1', 'Full candidate', 1, 'fullText', 'payload-1'),
                    ('grewia', 4, 'candidate-1', 'Bad candidate', 1, 'fullText', 'payload-4')
                    """
                )
                conn.commit()
            finally:
                conn.close()

            imported = Gen.import_reusable_results(str(target_db), str(source_db))
            reusable = Gen.load_reusable_task_keys(str(target_db), ["grewia"])

            self.assertEqual(imported["attack_result"], 2)
            self.assertEqual(imported["attack_candidate"], 1)
            self.assertEqual(reusable, {("grewia", 1), ("grewia", 2)})

            conn = sqlite3.connect(target_db)
            try:
                rows = conn.execute(
                    "SELECT id, status, memory_bytes, error_type FROM attack_result ORDER BY id"
                ).fetchall()
                candidates = conn.execute(
                    "SELECT id, candidate_id, full_text FROM attack_candidate ORDER BY id"
                ).fetchall()
            finally:
                conn.close()

            self.assertEqual(
                rows,
                [
                    (1, "completed", 4096, None),
                    (2, "failed", None, "tool_exception"),
                ],
            )
            self.assertEqual(candidates, [(1, "candidate-1", "payload-1")])


if __name__ == "__main__":
    unittest.main()
