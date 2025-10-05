# 🚀 Quick Start Guide

Get up and running with the AI Token Manager + Exo Bridge in **5 minutes**.

---

## Prerequisites

- **Python 3.12+** (required by Exo)
- **Git** for cloning repositories
- **Basic terminal knowledge**

---

## Step 1: Clone Parent Repositories

```bash
# Clone AI Token Manager
cd ~
git clone https://github.com/zebadiee/ai-token-manager.git

# Clone Exo
git clone https://github.com/exo-explore/exo.git
cd exo
pip install -e .
cd ~
```

---

## Step 2: Clone This Bridge

```bash
# Clone the bridge repository
git clone <your-repo-url> ai-token-exo-bridge
cd ai-token-exo-bridge
```

---

## Step 3: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run setup
python setup.py install
```

This will:
- ✓ Check Python version
- ✓ Verify parent repos exist
- ✓ Create config files
- ✓ Set up logging

---

## Step 4: Start Exo Cluster

```bash
# In a separate terminal
cd ~/exo
python3 main.py
```

Wait for Exo to start (you should see node discovery messages).

---

## Step 5: Test the Bridge

```bash
# Back in the bridge directory
cd ~/ai-token-exo-bridge

# Test connection
python src/bridge_manager.py --test
```

You should see:
```
✓ Bridge started successfully
Exo cluster: True
Healthy nodes: 1
Running test request...
Provider: Exo Local
Response: Hello! [...]
```

---

## Step 6: Start with HUD (Optional)

```bash
# Start bridge with monitoring dashboard
python src/bridge_manager.py --with-hud
```

Access the HUD at **http://localhost:8501**

---

## Step 7: Use in Your Code

```python
from src.bridge_manager import ExoBridgeManager

# Initialize
bridge = ExoBridgeManager()
bridge.start()

# Send request
result = bridge.chat_completion(
    messages=[{"role": "user", "content": "Hello!"}],
    model="llama-3.2-3b"
)

print(result['response'])
print(f"Provider: {result['provider_used']}")
print(f"Cost: ${result['cost']}")
```

---

## Common Issues

### "Exo cluster not detected"

```bash
# Check if Exo is running
curl http://localhost:8000/health

# If not, start it:
cd ~/exo
python3 main.py
```

### "Import errors"

```bash
# Ensure dependencies are installed
pip install -r requirements.txt

# Check Python version
python3 --version  # Must be 3.12+
```

### "No models available"

```bash
# Exo downloads models on first use
# Just make a request and it will download automatically
```

---

## Next Steps

1. **Explore examples**: `python examples/basic_usage.py`
2. **Read docs**: Check `docs/` directory
3. **Configure**: Edit `config/bridge_config.yaml`
4. **Contribute**: See `CONTRIBUTING.md`

---

## Quick Commands

```bash
# Test connection
python src/bridge_manager.py --test

# Start with HUD
python src/bridge_manager.py --with-hud

# Run examples
python examples/basic_usage.py

# Check status
curl http://localhost:8000/health
```

---

**Need help?** Open an issue or check the main [README.md](README.md)
