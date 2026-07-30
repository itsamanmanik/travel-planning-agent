#!/usr/bin/env bash
# run.sh  --  one-command start for Git Bash / Mac / Linux
# Usage:   ./run.sh      (if needed first:  chmod +x run.sh)

set -e
cd "$(dirname "$0")"

# Create the virtual environment on first run.
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python -m venv .venv
  ./.venv/Scripts/python.exe -m pip install --upgrade pip 2>/dev/null || \
    ./.venv/bin/python -m pip install --upgrade pip
fi

# Pick the right python path (Windows Git Bash vs Mac/Linux).
if [ -f "./.venv/Scripts/python.exe" ]; then
  PY="./.venv/Scripts/python.exe"      # Windows (Git Bash)
else
  PY="./.venv/bin/python"              # Mac / Linux
fi

# Install dependencies if needed.
"$PY" -m pip install -q -r requirements.txt

# Warn if the key is missing (the app still starts).
if [ ! -f ".env" ]; then
  echo "WARNING: no .env found. Copy .env.example to .env and add GROQ_API_KEY."
fi

echo "Starting the Travel Agent at http://localhost:8000 ..."
"$PY" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
