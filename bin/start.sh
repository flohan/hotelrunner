#!/usr/bin/env bash
set -euo pipefail
# Render setzt $PORT automatisch
exec gunicorn -w 2 -b 0.0.0.0:${PORT:-10000} app:app
