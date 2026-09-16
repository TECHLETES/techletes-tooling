"""Regression checks for the Techletes Codex V2 setup contract."""
from pathlib import Path
import unittest

PLUGIN = Path(__file__).resolve().parents[1]


class CodexV2ConfigTests(unittest.TestCase):
    def test_canonical_codex_docs_require_v2_features(self):
        paths = (
            PLUGIN / "codex" / "README.md",
            PLUGIN / "skills" / "using-superpowers" / "references" / "codex-tools.md",
        )
        for path in paths:
            with self.subTest(path=path):
                text = path.read_text()
                self.assertIn("multi_agent = true", text)
                self.assertIn("multi_agent_v2 = true", text)


if __name__ == "__main__":
    unittest.main()
