#!/bin/bash
# Secure Restart Script - Localhost Only

echo "=========================================================================="
echo "  SECURE RESTART - LOCALHOST LOCKDOWN MODE"
echo "=========================================================================="
echo ""

# Stop all existing services
echo "🛑 Stopping existing services..."
pkill -f "streamlit run" 2>/dev/null
pkill -f "token_manager_api" 2>/dev/null
sleep 2

echo "✅ Existing services stopped"
echo ""

# Apply localhost lockdown
echo "🔒 Applying localhost security lockdown..."
python3 enable_localhost_lockdown.py

if [ $? -ne 0 ]; then
    echo "❌ Failed to apply lockdown"
    exit 1
fi

echo ""
echo "🚀 Starting services in LOCALHOST-ONLY mode..."
echo "--------------------------------------------------------------------------"
echo ""

cd /Users/dadhoosband/ai-token-exo-bridge

# Start Streamlit bound to localhost only
echo "Starting Streamlit HUD (localhost:8501)..."
nohup streamlit run src/spiral_codex_hud.py \
    --server.port 8501 \
    --server.address 127.0.0.1 \
    --server.headless true \
    --browser.serverAddress 127.0.0.1 \
    --server.enableCORS false \
    --server.enableXsrfProtection true \
    > /tmp/spiral_codex_hud_secure.log 2>&1 &

STREAMLIT_PID=$!

sleep 3

# Check if running
if ps -p $STREAMLIT_PID > /dev/null; then
    echo "✅ Streamlit HUD started (localhost only)"
    echo "   PID: $STREAMLIT_PID"
    echo "   URL: http://127.0.0.1:8501"
    echo "   Logs: /tmp/spiral_codex_hud_secure.log"
    echo ""
else
    echo "❌ Failed to start Streamlit HUD"
    echo "   Check logs: /tmp/spiral_codex_hud_secure.log"
    exit 1
fi

# Show security status
echo "=========================================================================="
echo "  SECURITY STATUS"
echo "=========================================================================="
echo ""
echo "🔒 LOCALHOST LOCKDOWN: ACTIVE"
echo ""
echo "Protected Services:"
echo "  ✅ Streamlit HUD:  http://127.0.0.1:8501 (localhost only)"
echo "  ✅ Bind Address:   127.0.0.1 (no external access)"
echo "  ✅ CORS:           Disabled"
echo "  ✅ XSRF:           Enabled"
echo ""
echo "Security Features:"
echo "  🔒 External Access:     BLOCKED"
echo "  🔒 Network Binding:     127.0.0.1 only"
echo "  🔒 Remote Connections:  BLOCKED"
echo "  ✅ Local Browser:       ALLOWED"
echo ""
echo "Access Instructions:"
echo "  1. Open browser ON THIS MACHINE"
echo "  2. Navigate to: http://127.0.0.1:8501"
echo "  3. Remote access will NOT work (by design)"
echo ""
echo "View Logs:"
echo "  tail -f /tmp/spiral_codex_hud_secure.log"
echo ""
echo "Check Status:"
echo "  python3 enable_localhost_lockdown.py --status"
echo ""
echo "=========================================================================="
echo "  SECURE STARTUP COMPLETE"
echo "=========================================================================="
echo ""
