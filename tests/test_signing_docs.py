"""The release-key address in SIGNING.md must be the address the key carries.

The one-time setup told the reader to export ``release@bitseeker.com``. The
committed ``signing-key.asc`` is ``Bitseeker LLC <release@bitseeker.llc>``:
step 1 of the same section says so, and ``releases/PATCH-0.6.7.md:704`` records
the good signature made under that user id. Run literally, the export produced
nothing, so the documented way to reproduce ``signing-key.asc`` did not work.
The instance was corrected on ``main`` while the ``v0.6.8`` tag still carries
it. This module closes the class: a later revision cannot ship a setup step
that names an address the shipped key does not have.

The key is parsed here rather than handed to ``gpg``, because the assertion is
about the bytes the repository ships. A reviewer, or a runner with no keyring,
reaches the same answer offline.

Break-and-watch: put any other address back into either ``--export`` line and
``test_the_export_commands_name_the_shipped_key`` goes red; change the address
inside the armored key and the same test goes red, because the two sides are
compared against each other.
"""

from __future__ import annotations

import base64
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
KEY = ROOT / "signing-key.asc"
DOC = ROOT / "SIGNING.md"

BEGIN = "-----BEGIN PGP PUBLIC KEY BLOCK-----"
END = "-----END PGP PUBLIC KEY BLOCK-----"
USER_ID = 13
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
DOCUMENTED = re.compile(r"release@[A-Za-z0-9.-]+")


def armored_body(text: str) -> bytes:
    """The packet stream out of an ASCII-armored public key block."""
    lines = text.splitlines()
    try:
        start = lines.index(BEGIN) + 1
    except ValueError as exc:
        raise ValueError("signing-key.asc is not an armored public key block") from exc
    while start < len(lines) and lines[start].strip():
        start += 1                      # armor headers, e.g. "Version: ..."
    body = []
    for line in lines[start:]:
        if line.startswith(END):
            break
        if line.startswith("="):
            continue                    # the armor checksum
        body.append(line.strip())
    return base64.b64decode("".join(body))


def packets(data: bytes):
    """Walk OpenPGP packets: yields ``(tag, body)`` in stream order."""
    index = 0
    while index < len(data):
        tag_byte = data[index]
        index += 1
        if not tag_byte & 0x80:
            raise ValueError("packet is not tagged")
        if tag_byte & 0x40:             # new-format packet
            tag = tag_byte & 0x3F
            first = data[index]
            index += 1
            if first < 192:
                length = first
            elif first < 224:
                length = ((first - 192) << 8) + data[index] + 192
                index += 1
            elif first == 255:
                length = int.from_bytes(data[index:index + 4], "big")
                index += 4
            else:
                raise ValueError("partial body lengths are not expected in a key")
        else:                           # old-format packet
            tag = (tag_byte >> 2) & 0x0F
            kind = tag_byte & 0x03
            if kind == 0:
                length = data[index]
                index += 1
            elif kind == 1:
                length = int.from_bytes(data[index:index + 2], "big")
                index += 2
            elif kind == 2:
                length = int.from_bytes(data[index:index + 4], "big")
                index += 4
            else:
                length = len(data) - index
        yield tag, data[index:index + length]
        index += length


def key_addresses(path: Path) -> set:
    """Every e-mail address the key's user ids carry."""
    found = set()
    for tag, body in packets(armored_body(path.read_text(encoding="utf-8"))):
        if tag == USER_ID:
            found.update(EMAIL.findall(body.decode("utf-8", "replace")))
    return found


class SigningDocumentAddressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOC.read_text(encoding="utf-8")
        cls.shipped = key_addresses(KEY)

    def test_the_shipped_key_carries_a_user_id_address(self):
        self.assertTrue(
            self.shipped,
            "signing-key.asc yielded no user-id e-mail, so the comparison below "
            "would pass on two empty sets")

    def test_the_export_commands_name_the_shipped_key(self):  # CONTROL: CM-21
        documented = set(DOCUMENTED.findall(self.text))
        self.assertTrue(
            documented,
            "SIGNING.md no longer names a release address at all; the setup "
            "section has to say which identity the key is created under")
        self.assertEqual(
            documented, self.shipped,
            "every release address in SIGNING.md must be an address the shipped "
            "signing-key.asc actually carries. A setup step that names another "
            "address exports nothing, so the documented way to reproduce "
            "signing-key.asc stops working.")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
