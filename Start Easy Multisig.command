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
# The exact version is asserted, not merely the import: an older or substituted
# embit must not satisfy this check. requirements.lock carries the hash, so the
# install is verified rather than trusted to whatever the index serves.
if ! .venv/bin/python3 -c 'import importlib.metadata as m; raise SystemExit(0 if m.version("embit") == "0.8.2+besa.1" else 1)' >/dev/null 2>&1; then
  echo "Installing the hash-verified open-source descriptor library (first launch only)..."
  .venv/bin/python3 -m pip install --disable-pip-version-check --require-hashes -r requirements.lock
fi

echo "Opening the Bitcoin Easy Signer GUI in your browser..."
# Source mode runs the repository's own scripts/hwi_entry.py under this
# interpreter. Nothing is looked up on PATH, so a planted `hwi` there is never
# executed. The hwilib package that entry imports is pinned by hash in probe.py
# and a substituted copy is refused before it can see a wallet file or a
# signing request. Install hwi==3.2.0 into .venv — that is the library the
# entry point imports, not a separate program on your PATH.
.venv/bin/python3 gui.py
