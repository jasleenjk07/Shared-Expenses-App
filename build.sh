#!/usr/bin/env bash
set -euo pipefail
pip install -r backend/requirements.txt
pip install psycopg2-binary==2.9.9
cd frontend && npm install && npm run build
