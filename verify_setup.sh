#!/bin/bash
# Post-Push Verification Script
# Run this after git push to verify everything is working

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Spiral Codex HUD - Post-Push Verification                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check git status
echo "📋 Checking git status..."
cd ~/ai-token-exo-bridge
git status | grep -q "nothing to commit" && echo "✅ All changes committed" || echo "⚠️ Uncommitted changes remain"
echo ""

# Verify Python syntax
echo "🐍 Verifying Python syntax..."
python3 -m py_compile src/bridge_manager.py 2>/dev/null && echo "✅ bridge_manager.py OK" || echo "❌ bridge_manager.py has errors"
python3 -m py_compile src/spiral_codex_hud.py 2>/dev/null && echo "✅ spiral_codex_hud.py OK" || echo "❌ spiral_codex_hud.py has errors"
echo ""

# Check virtual environment
echo "🔧 Checking virtual environment..."
if [ -d ".venv" ]; then
    echo "✅ Virtual environment exists"
    source .venv/bin/activate
    streamlit --version 2>/dev/null && echo "✅ Streamlit installed" || echo "❌ Streamlit not found"
    python3 -c "import requests" 2>/dev/null && echo "✅ requests module available" || echo "❌ requests not installed"
else
    echo "❌ Virtual environment not found"
fi
echo ""

# Check configuration files
echo "📁 Checking configuration files..."
[ -f "config/bridge_config.yaml" ] && echo "✅ bridge_config.yaml exists" || echo "❌ bridge_config.yaml missing"
[ -f ~/.token_manager_config.json ] && echo "✅ token_manager_config.json exists" || echo "❌ token_manager_config.json missing"
echo ""

# Check scripts
echo "📜 Checking startup scripts..."
[ -x "start_hud.sh" ] && echo "✅ start_hud.sh executable" || echo "⚠️ start_hud.sh not executable"
[ -x "start_bridge.sh" ] && echo "✅ start_bridge.sh executable" || echo "⚠️ start_bridge.sh not executable"
echo ""

# Check provider configuration
echo "🌐 Checking provider configuration..."
if [ -f ~/.token_manager_config.json ]; then
    providers=$(python3 -c "import json; config = json.load(open('$HOME/.token_manager_config.json')); print(len([p for p in config.get('providers', []) if p.get('status') == 'active']))" 2>/dev/null)
    if [ ! -z "$providers" ]; then
        echo "✅ Found $providers active providers"
    else
        echo "⚠️ Could not read providers"
    fi
fi
echo ""

# Test import
echo "🧪 Testing bridge manager import..."
cd ~/ai-token-exo-bridge
source .venv/bin/activate 2>/dev/null
python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    from bridge_manager import ExoBridgeManager
    print('✅ Bridge manager imports successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
" 2>/dev/null
echo ""

# Summary
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Verification Complete                                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Ready to start? Run:"
echo "  cd ~/ai-token-exo-bridge"
echo "  ./start_hud.sh"
echo ""
echo "Or manually:"
echo "  cd ~/ai-token-exo-bridge && source .venv/bin/activate && streamlit run src/spiral_codex_hud.py"
echo ""
