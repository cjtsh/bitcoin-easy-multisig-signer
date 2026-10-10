#!/bin/zsh
# Double-click on a Mac. The browser UI runs only on this Mac (127.0.0.1).
set -e
cd -- "$(dirname -- "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required to run Bitcoin Easy Signer from source."
  echo "Install Python 3 from python.org, then double-click this launcher again."
  read -r "?Press Return to close..."
  exit 1
fi

if [ ! -x .venv/bin/python3 ]; then
  echo "Preparing the local Python environment (first launch only)..."
  python3 -m venv .venv
fi
# The exact versions are asserted, not merely the imports: an older or
# substituted build must not satisfy these checks. requirements-source.lock
# carries the hashes, so the install is verified rather than trusted to whatever
# the index serves. Both checks read distribution metadata with
# importlib.metadata and never import the package — which matters for hwilib:
# probe.py hashes it and refuses a substituted copy, so the launcher must not be
# the thing that executes it first. The hwi check is what makes a first launch
# that predates this line gain the device library instead of skipping the install.
if ! .venv/bin/python3 -c 'import importlib.metadata as m; raise SystemExit(0 if m.version("embit") == "0.8.2+besa.1" else 1)' >/dev/null 2>&1 \
   || ! .venv/bin/python3 -c 'import importlib.metadata as m; raise SystemExit(0 if m.version("hwi") == "3.2.0" else 1)' >/dev/null 2>&1; then
  echo "Installing the hash-verified dependencies (first launch only)..."
  .venv/bin/python3 -m pip install --disable-pip-version-check --require-hashes -r requirements-source.lock
fi

echo "Opening the Bitcoin Easy Signer GUI in your browser..."
# Source mode runs the repository's own scripts/hwi_entry.py under this
# interpreter. Nothing is looked up on PATH, so a planted `hwi` there is never
# executed. The hwilib package that entry imports is pinned by hash in probe.py
# and a substituted copy is refused before it can see a wallet file or a
# signing request. requirements-source.lock installs hwi 3.2.0 into .venv —
# that is the library the entry point imports, not a separate program on your
# PATH. Its pins are the reviewed desktop lock's, so source mode and the
# released bundle cannot run two different builds of the same library.
.venv/bin/python3 gui.py
