#!/bin/bash
set -e
cd "$(dirname "$0")"
export PYTHONPATH=.

if [ ! -d "venv" ]; then
  python3 -m venv venv
  source venv/bin/activate
  pip install -r backend/requirements.txt
else
  source venv/bin/activate
fi

python backend/app.py
