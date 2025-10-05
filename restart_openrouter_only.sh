#!/bin/bash
# Restart Spiral Codex HUD with OpenRouter-Only Configuration

echo "=========================================================================="
echo "  RESTARTING SPIRAL CODEX HUD - OPENROUTER ONLY MODE"
echo "=========================================================================="
echo ""

# Stop existing Streamlit process
echo "🛑 Stopping existing Streamlit process..."
pkill -f "streamlit run src/spiral_codex_hud.py" 2>/dev/null
sleep 2

# Check if stopped
if pgrep -f "streamlit run" > /dev/null; then
    echo "⚠️  Streamlit still running, force killing..."
    pkill -9 -f "streamlit run"
    sleep 1
fi

echo "✅ Existing process stopped"
echo ""

# Show current provider status
echo "📊 Current Provider Configuration:"
echo "--------------------------------------------------------------------------"
python3 disable_huggingface.py --status
echo ""

# Start Streamlit
echo "🚀 Starting Spiral Codex HUD..."
echo "--------------------------------------------------------------------------"
echo ""

cd /Users/dadhoosband/ai-token-exo-bridge

# Start in background
nohup streamlit run src/spiral_codex_hud.py --server.port 8501 > /tmp/spiral_codex_hud.log 2>&1 &

# Get PID
STREAMLIT_PID=$!

sleep 3

# Check if running
if ps -p $STREAMLIT_PID > /dev/null; then
    echo "✅ Spiral Codex HUD started successfully"
    echo "   PID: $STREAMLIT_PID"
    echo "   URL: http://localhost:8501"
    echo "   Logs: /tmp/spiral_codex_hud.log"
    echo ""
    echo "Expected Provider Status:"
    echo "  ✅ OpenRouter - ACTIVE & HEALTHY (326 models available)"
    echo "  ⚠️  HuggingFace - INACTIVE (temporarily disabled)"
    echo "  ℹ️  Exo Local - DISABLED (can be enabled if needed)"
    echo ""
    echo "Open your browser to: http://localhost:8501"
    echo ""
    echo "To view logs in real-time:"
    echo "  tail -f /tmp/spiral_codex_hud.log"
    echo ""
else
    echo "❌ Failed to start Spiral Codex HUD"
    echo "   Check logs: /tmp/spiral_codex_hud.log"
    echo ""
    exit 1
fi

echo "=========================================================================="
echo "  STARTUP COMPLETE"
echo "=========================================================================="
echo ""
echo "Next Steps:"
echo "  1. Open http://localhost:8501 in your browser"
echo "  2. Navigate to 'Providers' tab"
echo "  3. Verify OpenRouter shows as HEALTHY"
echo "  4. Start using OpenRouter models for all inference"
echo ""
echo "To re-enable HuggingFace later:"
echo "  python enable_huggingface.py YOUR_NEW_HF_TOKEN"
echo ""
