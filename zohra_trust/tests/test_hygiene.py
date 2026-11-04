"""Things that must never come back."""

import re
from pathlib import Path

from frappe.tests.utils import FrappeTestCase

APP_ROOT = Path(__file__).resolve().parents[2]  # the app's repo folder
SOURCE = {".py", ".js", ".json", ".html", ".css", ".txt", ".yml", ".yaml", ".csv", ".md"}
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".github"}
# The change request that orders the removal has to name what it removes, and this test names it too.
SKIP_FILES = {"ZOHRA_CHANGE_REQUEST_1.md", "test_hygiene.py"}
FORBIDDEN = re.compile(r"\bnios\b|embassy", re.I)


class TestNoNiosOrEmbassy(FrappeTestCase):
	def test_no_source_or_fixture_file_mentions_nios_or_embassy(self):
		hits = []
		for path in APP_ROOT.rglob("*"):
			if not path.is_file() or path.suffix.lower() not in SOURCE or path.name in SKIP_FILES:
				continue
			if SKIP_DIRS & set(path.relative_to(APP_ROOT).parts):
				continue
			for number, line in enumerate(path.read_text(errors="ignore").splitlines(), 1):
				if FORBIDDEN.search(line):
					hits.append(f"{path.relative_to(APP_ROOT)}:{number}: {line.strip()[:80]}")
		self.assertEqual(hits, [])
		self.assertTrue((APP_ROOT / "zohra_trust" / "fixtures" / "custom_field.json").exists())  # the scan really reached the fixtures
