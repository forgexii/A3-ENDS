#!/usr/bin/env bash
# ==============================================================================
# A3-ENDS: Adaptive AI-Driven Enterprise Network Defense System
# Unified System Launch Script
# ==============================================================================

set -e

# Resolve script directory (A3-ENDS root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Locate virtual environment
if [ -d "$SCRIPT_DIR/../venv" ]; then
    VENV_PATH="$SCRIPT_DIR/../venv"
elif [ -d "$SCRIPT_DIR/venv" ]; then
    VENV_PATH="$SCRIPT_DIR/venv"
else
    echo "[!] Virtual environment not found in $SCRIPT_DIR/venv or $SCRIPT_DIR/../venv"
    echo "[!] Please create and activate a virtual environment first."
    exit 1
fi

source "$VENV_PATH/bin/activate"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
export MPLCONFIGDIR="/tmp/matplotlib"

# Ensure backend database directory exists
mkdir -p "$SCRIPT_DIR/backend/data"

# Help message
show_help() {
    cat << EOF
A3-ENDS Startup Utility

Usage:
  ./start_all.sh [MODE]

Available Modes:
  --all       (Default) Launch Backend, Sniffer/Runner, and Desktop GUI together.
              Background services are automatically stopped when GUI exits or on Ctrl+C.
  --backend   Launch only the FastAPI Orchestration Server on 127.0.0.1:8000.
  --sniffer   Launch only the Real-time Packet Sniffer / Flow Runner.
              (Run with sudo if live NIC packet capture is required).
  --gui       Launch only the PyQt6 Analyst Desktop Dashboard.
  --help      Show this help message.

Examples:
  ./start_all.sh            # Starts the full system suite
  ./start_all.sh --backend  # Starts only the FastAPI server
  sudo ./start_all.sh --sniffer # Starts sniffer with root permissions for live capture

Note:
  Attack injection (generate_attack_samples.py) is intentionally NOT included
  in start_all.sh. To inject test attack vectors on demand, run:
    python generate_attack_samples.py --help
EOF
}

MODE="${1:---all}"

case "$MODE" in
    --help|-h)
        show_help
        exit 0
        ;;
    --backend)
        echo "[*] Starting A3-ENDS FastAPI Backend Server on http://127.0.0.1:8000..."
        exec uvicorn backend.main:app --host 127.0.0.1 --port 8000
        ;;
    --sniffer)
        echo "[*] Starting A3-ENDS Real-time Flow Runner / Sniffer..."
        exec python realtime/runner.py
        ;;
    --gui)
        echo "[*] Starting A3-ENDS PyQt6 Analyst Desktop Dashboard..."
        exec python a3ends-desktop/main.py
        ;;
    --all)
        echo "=================================================================="
        echo "  A3-ENDS: Adaptive Enterprise Network Defense System"
        echo "=================================================================="
        
        PIDS=()
        cleanup() {
            echo ""
            echo "[*] Shutting down A3-ENDS services..."
            for pid in "${PIDS[@]}"; do
                if kill -0 "$pid" 2>/dev/null; then
                    echo "    - Terminating process PID $pid"
                    kill -TERM "$pid" 2>/dev/null || true
                fi
            done
            wait 2>/dev/null || true
            echo "[✓] All A3-ENDS services stopped."
        }
        trap cleanup EXIT INT TERM

        # 1. Start Backend API
        echo "[1/3] Starting FastAPI Backend API (127.0.0.1:8000)..."
        uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
        BACKEND_PID=$!
        PIDS+=("$BACKEND_PID")

        # Wait for backend to become ready
        echo "[*] Waiting for backend AI pipeline to initialize..."
        MAX_WAIT=20
        WAIT_COUNT=0
        while ! curl -s http://127.0.0.1:8000/api/health | grep -q '"status":"healthy"'; do
            sleep 1
            WAIT_COUNT=$((WAIT_COUNT + 1))
            if [ "$WAIT_COUNT" -ge "$MAX_WAIT" ]; then
                echo "[!] Backend failed to report healthy within $MAX_WAIT seconds."
                exit 1
            fi
        done
        echo "[✓] Backend is online and ready."

        # 2. Start Real-time Sniffer / Runner
        echo "[2/3] Starting Real-time Packet Capture / Flow Runner..."
        python realtime/runner.py &
        RUNNER_PID=$!
        PIDS+=("$RUNNER_PID")
        echo "[✓] Flow runner active (PID: $RUNNER_PID)."

        # 3. Start Desktop GUI Dashboard
        echo "[3/3] Launching PyQt6 Analyst Desktop Dashboard..."
        python a3ends-desktop/main.py

        echo "[*] Dashboard window closed."
        ;;
    *)
        echo "[!] Unknown option: $MODE"
        show_help
        exit 1
        ;;
esac
