#!/bin/bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "$GROQ_API_KEY" ]; then
  echo "GROQ_API_KEY is not set."
  echo "Run: export GROQ_API_KEY=\"your-groq-key\""
  exit 1
fi

cd "$ROOT_DIR"
source venv/bin/activate

PORT="${PORT:-5050}"
VITE_API_URL="${VITE_API_URL:-http://localhost:$PORT}"
export PORT
export VITE_API_URL

python -m backend.api &
BACKEND_PID=$!

cleanup() {
  kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT

cd "$ROOT_DIR/frontend"
pnpm dev
