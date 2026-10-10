"""Print the SHA-256 of every file in vendor/, in sha256sum's own format.

CT-88: the digests in `vendor/README.md` were prose and nothing checked them.
This is the command that reproduces them. After deliberately replacing a
vendored file, run it, update the prose in `vendor/README.md`, and update
`DIGESTS` in `tests/test_vendor_pins.py` in the same commit -- all three are
the same claim about the same bytes.

    python scripts/vendor-digests.py [directory]
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def digests(directory: Path) -> dict[str, str]:
    """name -> SHA-256 for every regular file in the directory."""
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.iterdir())
        if path.is_file()
    }


def main(argv: list[str]) -> int:
    directory = Path(argv[1]) if len(argv) > 1 else Path("vendor")
    if not directory.is_dir():
        print(f"{directory} is not a directory", file=sys.stderr)
        return 2
    for name, digest in sorted(digests(directory).items()):
        print(f"{digest}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
