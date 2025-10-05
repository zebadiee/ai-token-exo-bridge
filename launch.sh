#!/bin/bash
# Enhanced Launcher for AI Token Manager + Exo Bridge with ReliaKit
# Starts Exo cluster, bridge manager, and Spiral Codex HUD with self-healing

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  AI Token Manager + Exo Bridge with ReliaKit Self-Healing   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check/setup virtual environment
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo -e "${YELLOW}Setting up virtual environment...${NC}"
    python3 -m venv "$SCRIPT_DIR/.venv"
    source "$SCRIPT_DIR/.venv/bin/activate"
    pip install --upgrade pip --quiet
    pip install -r "$SCRIPT_DIR/requirements.txt" --quiet
    echo -e "${GREEN}✓ Virtual environment created and dependencies installed${NC}"
else
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

# Verify Streamlit is available
if ! command -v streamlit &> /dev/null; then
    echo -e "${RED}✗ Streamlit not found in virtual environment${NC}"
    echo "Installing dependencies..."
    pip install -r "$SCRIPT_DIR/requirements.txt" --quiet
fi

# Check if Exo is running
echo -e "${YELLOW}Checking Exo cluster status...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Exo cluster is running${NC}"
else
    echo -e "${YELLOW}⚠ Exo cluster not detected${NC}"
    echo ""
    echo "Starting Exo cluster in background..."
    
    if [ -d "$HOME/exo" ]; then
        cd "$HOME/exo"
        nohup python3 main.py > /tmp/exo_cluster.log 2>&1 &
        EXO_PID=$!
        echo "Exo PID: $EXO_PID"
        
        echo "Waiting for Exo to start..."
        for i in {1..30}; do
            if curl -s http://localhost:8000/health > /dev/null 2>&1; then
                echo -e "${GREEN}✓ Exo cluster started${NC}"
                break
            fi
            sleep 1
            echo -n "."
        done
        echo ""
    else
        echo -e "${RED}✗ Exo not found at ~/exo${NC}"
        echo "Please install: git clone https://github.com/exo-explore/exo.git ~/exo"
        exit 1
    fi
fi

cd "$SCRIPT_DIR"

# Parse arguments
MODE="full"
if [ $# -gt 0 ]; then
    MODE="$1"
fi

case $MODE in
    "hud")
        echo -e "${BLUE}Starting Spiral Codex HUD only...${NC}"
        streamlit run src/spiral_codex_hud.py --server.port 8501
        ;;
    
    "bridge")
        echo -e "${BLUE}Starting Bridge Manager only...${NC}"
        python src/bridge_manager.py --with-reliakit
        ;;
    
    "test")
        echo -e "${BLUE}Running integration test...${NC}"
        python src/bridge_manager.py --test
        ;;
    
    "full"|*)
        echo -e "${BLUE}Starting Full Stack...${NC}"
        echo ""
        echo "Components:"
        echo "  1. ✓ Exo Cluster (http://localhost:8000)"
        echo "  2. → Bridge Manager (starting...)"
        echo "  3. → Spiral Codex HUD (http://localhost:8501)"
        echo "  4. → ReliaKit Self-Healing (auto-enabled)"
        echo ""
        
        # Start bridge in background
        echo -e "${YELLOW}Starting bridge manager...${NC}"
        nohup python src/bridge_manager.py > /tmp/bridge_manager.log 2>&1 &
        BRIDGE_PID=$!
        echo "Bridge PID: $BRIDGE_PID"
        sleep 2
        
        # Start HUD in foreground
        echo -e "${GREEN}Starting Spiral Codex HUD...${NC}"
        echo ""
        echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                                                              ║${NC}"
        echo -e "${GREEN}║  🌀 Spiral Codex HUD starting...                            ║${NC}"
        echo -e "${GREEN}║                                                              ║${NC}"
        echo -e "${GREEN}║  Access at: http://localhost:8501                           ║${NC}"
        echo -e "${GREEN}║                                                              ║${NC}"
        echo -e "${GREEN}║  Features:                                                   ║${NC}"
        echo -e "${GREEN}║  • Real-time Exo cluster monitoring                         ║${NC}"
        echo -e "${GREEN}║  • ReliaKit self-healing events                             ║${NC}"
        echo -e "${GREEN}║  • Automatic failover tracking                              ║${NC}"
        echo -e "${GREEN}║  • Interactive model testing                                 ║${NC}"
        echo -e "${GREEN}║                                                              ║${NC}"
        echo -e "${GREEN}║  Press Ctrl+C to stop                                        ║${NC}"
        echo -e "${GREEN}║                                                              ║${NC}"
        echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        
        streamlit run src/spiral_codex_hud.py --server.port 8501
        
        # Cleanup on exit
        echo ""
        echo -e "${YELLOW}Shutting down...${NC}"
        kill $BRIDGE_PID 2>/dev/null || true
        ;;
esac
