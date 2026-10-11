"""The download page names the version this tree publishes.

CT-04: the `v0.6.8` tag's `docs/index.html` pointed at the *previous* release's
assets until it was corrected on `main` after publication. The tag is immutable,
so the page a reader lands on has to be right before the tag is cut. GitHub Pages
serves the committed file, so no template step can substitute the version at
deploy time; this test stands in for that step. It fails the build the moment the
page and `version.py` disagree, which is the moment the tag would ship a page
that sends a visitor to the wrong bytes.

The test reads text, so it cannot see whether a link resolves -- only that the
page names the version the tree is about to publish, that every platform still
appears, and that the finding record it points at is this cycle's.
"""

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "index.html"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from version import APP_VERSION  # noqa: E402

JSON_LD = re.compile(
    r'<script type="application/ld\+json">(.*?)</script>', re.S
)
DOWNLOAD = re.compile(r"releases/download/v([0-9]+\.[0-9]+\.[0-9]+)/")
ASSET = re.compile(
    r"releases/download/v([0-9]+\.[0-9]+\.[0-9]+)/Bitcoin-Easy-Signer-v[0-9]+\.[0-9]+\.[0-9]+-([A-Za-z0-9._-]+)"
)
PATCH_LINK = re.compile(r"releases/PATCH-([0-9]+\.[0-9]+\.[0-9]+)\.md")
VERSION_LABEL = re.compile(r"Version ([0-9]+\.[0-9]+\.[0-9]+)")

# The artifacts the release pipeline publishes and the page offers.
PLATFORM_ASSETS = ("macOS.dmg", "windows-x64.zip", "linux-x86_64.AppImage")


class DocsVersionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGE.read_text(encoding="utf-8")

    def _mismatches(self, pattern, where):
        found = pattern.findall(self.page)
        self.assertTrue(found, f"{where}: the page names no version at all")
        wrong = sorted({version for version in found if version != APP_VERSION})
        self.assertEqual(
            wrong,
            [],
            f"{where} names a version other than {APP_VERSION}: {wrong}",
        )

    def test_every_download_url_names_the_current_version(self):
        self._mismatches(DOWNLOAD, "docs/index.html download URLs")

    def test_every_visible_version_label_names_the_current_version(self):
        self._mismatches(VERSION_LABEL, "docs/index.html version labels")

    def test_the_finding_record_link_names_the_current_cycle(self):
        self._mismatches(PATCH_LINK, "docs/index.html patch-record links")

    def test_the_json_ld_names_the_current_version(self):
        documents = [json.loads(block) for block in JSON_LD.findall(self.page)]
        applications = [
            document
            for document in documents
            if document.get("@type") == "SoftwareApplication"
        ]
        self.assertEqual(
            len(applications), 1, "expected exactly one SoftwareApplication block"
        )
        application = applications[0]
        self.assertEqual(
            application.get("softwareVersion"),
            APP_VERSION,
            "the JSON-LD softwareVersion is not the version this tree publishes",
        )
        self.assertRegex(
            application.get("downloadUrl", ""),
            rf"releases/download/v{re.escape(APP_VERSION)}/",
            "the JSON-LD downloadUrl points at another release",
        )

    def test_every_platform_still_has_a_download_link(self):
        offered = {asset for version, asset in ASSET.findall(self.page)}
        missing = sorted(set(PLATFORM_ASSETS) - offered)
        self.assertEqual(
            missing,
            [],
            "a platform the release publishes has no link on the download page: "
            f"{missing}",
        )


if __name__ == "__main__":
    unittest.main()
