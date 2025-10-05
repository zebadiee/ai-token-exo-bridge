#!/bin/bash
# Quick Start Script for AI Token Exo Bridge
# Run this to start both Exo cluster and the Bridge HUD

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Starting AI Token Manager + Exo Bridge                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if Exo is already running
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Exo cluster already running on port 8000"
else
    echo "🚀 Starting Exo cluster..."
    echo "   (This will run in the background)"
    
    # Start Exo in background
    cd ~/exo
    source .venv/bin/activate
    nohup python3 exo/main.py --chatgpt-api-port 8000 > /tmp/exo.log 2>&1 &
    EXO_PID=$!
    
    echo "   Exo starting (PID: $EXO_PID)..."
    sleep 3
    
    # Verify it started
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo "   ✅ Exo cluster started successfully"
    else
        echo "   ⚠️  Exo may still be starting (check /tmp/exo.log)"
    fi
fi

echo ""
echo "🌀 Starting Bridge with Spiral Codex HUD..."
echo ""

cd ~/ai-token-exo-bridge

# Activate virtual environment and start HUD
source .venv/bin/activate
streamlit run src/spiral_codex_hud.py

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Bridge stopped                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
