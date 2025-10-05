# 🌉 ai-token-exo-bridge

**Zero-modification adapter bridging [ai-token-manager](https://github.com/zebadiee/ai-token-manager) with [Exo](https://github.com/exo-explore/exo) distributed AI cluster.**

## 🚀 5-Minute Setup

```bash
# 1. Clone parent repos
git clone https://github.com/zebadiee/ai-token-manager.git ~/ai-token-manager
git clone https://github.com/exo-explore/exo.git ~/exo
cd ~/exo && pip install -e .

# 2. Clone this bridge
git clone <repo-url> ~/ai-token-exo-bridge
cd ~/ai-token-exo-bridge
pip install -r requirements.txt
python setup.py install

# 3. Start Exo (separate terminal)
cd ~/exo && python3 main.py

# 4. Test bridge
python src/bridge_manager.py --test

# 5. Launch HUD (optional)
python src/bridge_manager.py --with-hud
# Visit http://localhost:8501
```

## 💻 Usage

```python
from src.bridge_manager import ExoBridgeManager

bridge = ExoBridgeManager()
bridge.start()

result = bridge.chat_completion(
    messages=[{"role": "user", "content": "Hello!"}],
    model="llama-3.2-3b"
)
# Uses Exo (free) if available, auto-fails to cloud if not
```

## ✨ Features

- 🆓 Zero-cost local inference via Exo
- 🔄 Automatic cloud failover
- 📊 Real-time monitoring HUD
- 🛡️ Self-healing with health checks
- 🔌 Zero changes to parent repos
- 🎯 ChatGPT-compatible API

## 📚 Docs

- [Quick Start](QUICKSTART.md) - 5 minutes to running
- [Full README](README.md) - Complete documentation
- [Integration Summary](INTEGRATION_SUMMARY.md) - Architecture & design

## 🤝 Contributing

This is a bridge/adapter repo - improvements welcome! Keep it clean, don't modify parent repos.

**License**: MIT
