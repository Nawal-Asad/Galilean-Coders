#!/usr/bin/env bash
# ==============================================================================
# SPHEREx Sky Explorer — Unified Single-Command Startup Script
# ==============================================================================
# Launches the complete application (Flask frontend + FastAPI backend)
# under a single unified URL (default: http://127.0.0.1:8000).
#
# Usage:
#   ./start.sh                  # Start on default 127.0.0.1:8000
#   PORT=8080 ./start.sh        # Start on a custom port
#   HOST=0.0.0.0 ./start.sh     # Listen on all network interfaces
#   ./start.sh --reload         # Enable auto-reload for development
#   ./start.sh --dual           # Optional: Run as separate processes (5000 + 8000)
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Locate the Python interpreter
if [[ -f "$SCRIPT_DIR/.venv/bin/python" ]]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="$(command -v python3)"
elif command -v python &>/dev/null; then
    PYTHON_BIN="$(command -v python)"
else
    echo "ERROR: Python 3 could not be found. Please install Python or set up .venv." >&2
    exit 1
fi

# 2. Configuration defaults (values from .env are loaded by spherex.config)
CONFIG_HOST="$("$PYTHON_BIN" -c 'from spherex.config import HOST; print(HOST)')"
CONFIG_PORT="$("$PYTHON_BIN" -c 'from spherex.config import PORT; print(PORT)')"
HOST="${HOST:-$CONFIG_HOST}"
PORT="${PORT:-$CONFIG_PORT}"
DUAL_MODE=false
EXTRA_ARGS=()

for arg in "$@"; do
    if [[ "$arg" == "--dual" ]]; then
        DUAL_MODE=true
    else
        EXTRA_ARGS+=("$arg")
    fi
done

# Function to check whether a port is available
is_port_in_use() {
    local host="$1"
    local port="$2"
    ! "$PYTHON_BIN" -c "import socket; s = socket.socket(); s.bind(('$host', int('$port'))); s.close()" 2>/dev/null
}

# ------------------------------------------------------------------------------
# Mode A: Dual-process Mode (Legacy fallback)
# ------------------------------------------------------------------------------
if [[ "$DUAL_MODE" == "true" ]]; then
    echo "================================================================="
    echo "  SPHEREx Sky Explorer — Dual Process Mode"
    echo "================================================================="
    FRONTEND_PORT="${FRONTEND_PORT:-5000}"
    BACKEND_PORT="${BACKEND_PORT:-$PORT}"

    if is_port_in_use "$HOST" "$BACKEND_PORT"; then
        echo "ERROR: Backend port $BACKEND_PORT is already in use on $HOST." >&2
        echo "Stop the process using port $BACKEND_PORT or set BACKEND_PORT=<port>." >&2
        exit 1
    fi

    if is_port_in_use "0.0.0.0" "$FRONTEND_PORT"; then
        echo "WARNING: Frontend port $FRONTEND_PORT is in use. Switching to 5001."
        FRONTEND_PORT=5001
    fi

    echo "Starting FastAPI backend on http://${HOST}:${BACKEND_PORT}..."
    "$PYTHON_BIN" -m uvicorn backend.main:app --host "$HOST" --port "$BACKEND_PORT" "${EXTRA_ARGS[@]}" &
    BACKEND_PID=$!

    echo "Starting Flask frontend on http://127.0.0.1:${FRONTEND_PORT}..."
    FLASK_RUN_PORT="$FRONTEND_PORT" "$PYTHON_BIN" -c "from frontend.app import app; app.run(host='0.0.0.0', port=$FRONTEND_PORT)" &
    FRONTEND_PID=$!

    cleanup_dual() {
        echo ""
        echo "Shutting down services..."
        kill -TERM "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
        wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
        echo "Services stopped cleanly."
    }
    trap cleanup_dual INT TERM EXIT

    echo ""
    echo "Services are running:"
    echo "  - Frontend: http://127.0.0.1:${FRONTEND_PORT}/"
    echo "  - Explorer: http://127.0.0.1:${FRONTEND_PORT}/explorer"
    echo "  - Backend:  http://${HOST}:${BACKEND_PORT}/"
    echo "Press Ctrl+C to stop both services."
    wait
    exit 0
fi

# ------------------------------------------------------------------------------
# Mode B: Unified Single-Application Mode (Recommended)
# ------------------------------------------------------------------------------
if is_port_in_use "$HOST" "$PORT"; then
    echo "ERROR: Port $PORT is already in use on $HOST." >&2
    echo "" >&2
    echo "You can either:" >&2
    echo "  1) Stop the running process on port $PORT" >&2
    echo "  2) Choose a different port:  PORT=8080 ./start.sh" >&2
    exit 1
fi

echo "================================================================="
echo "  🚀 SPHEREx Sky Explorer — Unified Application"
echo "================================================================="
echo "  Python:    $("$PYTHON_BIN" --version 2>&1)"
echo "  Host:      $HOST"
echo "  Port:      $PORT"
echo ""
echo "  Available URLs (all on single port $PORT):"
echo "  ➜ Mission Landing Page: http://${HOST}:${PORT}/"
echo "  ➜ Data Explorer:        http://${HOST}:${PORT}/explorer"
echo "  ➜ Live Satellite Orbit: http://${HOST}:${PORT}/tracker"
echo "  ➜ FITS Image Viewer:    http://${HOST}:${PORT}/fits"
echo "  ➜ Backend API Docs:     http://${HOST}:${PORT}/docs"
echo "  ➜ Backend API Status:   http://${HOST}:${PORT}/api"
echo "================================================================="
echo "Press Ctrl+C at any time to shut down the server."
echo ""

# Execute uvicorn with the unified application
exec "$PYTHON_BIN" -m uvicorn unified_app:app --host "$HOST" --port "$PORT" "${EXTRA_ARGS[@]}"
