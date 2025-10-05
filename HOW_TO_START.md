# 🚀 How to Start the Spiral Codex HUD

## Quick Start (Recommended)

### Method 1: One-Line Start
```bash
cd ~/ai-token-exo-bridge && source .venv/bin/activate && streamlit run src/spiral_codex_hud.py
```

### Method 2: Use the Script
```bash
cd ~/ai-token-exo-bridge
./start_hud.sh
```

### Method 3: Full Setup (Exo + HUD)
```bash
cd ~/ai-token-exo-bridge
./start_bridge.sh
```

## Why "command not found: streamlit"?

Streamlit is installed in the **virtual environment** (`.venv`), not globally.

You must **activate the virtual environment first**:
```bash
source .venv/bin/activate
```

Then you can run:
```bash
streamlit run src/spiral_codex_hud.py
```

## Step-by-Step

### Terminal 1: Start Exo (if not running)
```bash
cd ~/exo
source .venv/bin/activate
python3 exo/main.py --chatgpt-api-port 8000
```

### Terminal 2: Start HUD
```bash
cd ~/ai-token-exo-bridge
source .venv/bin/activate
streamlit run src/spiral_codex_hud.py
```

### Browser
Open: **http://localhost:8501**

## Verify Setup

### Check Virtual Environment
```bash
cd ~/ai-token-exo-bridge
source .venv/bin/activate
which streamlit
# Should output: /Users/dadhoosband/ai-token-exo-bridge/.venv/bin/streamlit
```

### Check Streamlit Version
```bash
cd ~/ai-token-exo-bridge
source .venv/bin/activate
streamlit --version
# Should output: Streamlit, version 1.50.0
```

### List Installed Packages
```bash
cd ~/ai-token-exo-bridge
source .venv/bin/activate
pip list | grep streamlit
```

## Troubleshooting

### "streamlit: command not found"
**Problem:** Virtual environment not activated

**Solution:**
```bash
cd ~/ai-token-exo-bridge
source .venv/bin/activate
```

### "No module named 'streamlit'"
**Problem:** Streamlit not installed in venv

**Solution:**
```bash
cd ~/ai-token-exo-bridge
source .venv/bin/activate
pip install streamlit plotly pandas
```

### Port Already in Use
**Problem:** Another app using port 8501

**Solution:**
```bash
# Use different port
streamlit run src/spiral_codex_hud.py --server.port 8502
```

## Quick Reference

### Activate Venv
```bash
cd ~/ai-token-exo-bridge
source .venv/bin/activate
```

### Deactivate Venv
```bash
deactivate
```

### Start HUD
```bash
# After activating venv:
streamlit run src/spiral_codex_hud.py
```

### Stop HUD
Press `Ctrl+C` in the terminal

## All-in-One Command

```bash
cd ~/ai-token-exo-bridge && source .venv/bin/activate && streamlit run src/spiral_codex_hud.py
```

Copy and paste this into your terminal! 🚀
