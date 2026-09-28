#!/bin/zsh
# Double-click on a Mac. The browser UI runs only on this Mac (127.0.0.1).
set -e
cd -- "$(dirname -- "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required for this experimental preview."
  echo "Install Python 3 from python.org, then double-click this launcher again."
  read -r "?Press Return to close..."
  exit 1
fi

if [ ! -x .venv/bin/python3 ]; then
  echo "Preparing the local Python environment (first launch only)..."
  python3 -m venv .venv
fi
if ! .venv/bin/python3 -c 'import embit' >/dev/null 2>&1; then
  echo "Installing the pinned open-source descriptor library (first launch only)..."
  .venv/bin/python3 -m pip install --disable-pip-version-check -r requirements.txt
fi

echo "Opening the Testnet4 wallet GUI in your browser..."
.venv/bin/python3 gui.py