#!/usr/bin/env bash
# Production-style API (no --reload): one process, one MQTT subscriber.
set -euo pipefail
cd "$(dirname "$0")/.."
exec uvicorn main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
