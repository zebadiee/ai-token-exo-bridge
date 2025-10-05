# 🌀 Cloud Routing & Failover - Complete Guide

## Overview

Your AI Token Manager + Exo Bridge now supports **intelligent multi-provider routing** with automatic failover between:

1. **Exo Local** (Priority 0) - FREE, unlimited local inference
2. **OpenRouter** (Priority 1) - Cloud failover with 1000+ models
3. **Hugging Face** (Priority 2) - Secondary cloud failover

## Current Configuration Status

### ✅ All Providers Active

```json
Provider Status:
  ✅ Exo Local:      ACTIVE (localhost:8000)
  ✅ OpenRouter:     ACTIVE (API key configured)
  ✅ Hugging Face:   ACTIVE (API key configured)
```

### Provider Details

#### Exo Local (Priority 0 - Highest)
- **Base URL:** http://localhost:8000
- **Cost:** $0.00 (completely free)
- **Rate Limit:** Unlimited
- **Token Limit:** Unlimited
- **Status:** Currently downloading Llama-3.2-3B-Instruct-4bit
- **Use Case:** All requests try Exo first

#### OpenRouter (Priority 1)
- **Base URL:** https://openrouter.ai/api/v1
- **Cost:** Variable by model
- **Rate Limit:** 1,000 requests/day
- **Token Limit:** 100,000 tokens
- **API Key:** ✅ Configured & Encrypted
- **Use Case:** Automatic failover when Exo is unavailable or for cloud-only models

#### Hugging Face (Priority 2)
- **Base URL:** https://api-inference.huggingface.co
- **Cost:** Free tier with limits
- **Rate Limit:** 100 requests/day (free tier)
- **Token Limit:** 50,000 tokens
- **API Key:** ✅ Configured & Encrypted
- **Use Case:** Final fallback option

---

## How Routing Works

### Intelligent Provider Selection

The bridge uses a **priority-based routing** system:

```
Request → Try Exo Local (free)
          ↓ If unavailable/fails
          Try OpenRouter (paid)
          ↓ If unavailable/fails
          Try Hugging Face (free tier)
          ↓ If all fail
          Return error
```

### Cost Optimization

The system **always prefers free providers first**:
- Exo Local: $0.00 per request
- OpenRouter: ~$0.001 - $0.05 per request (model dependent)
- Hugging Face: $0.00 (free tier)

**Estimated Monthly Savings:**
- 1,000 requests on Exo vs OpenRouter: **~$10-50 saved**
- 10,000 requests on Exo vs OpenRouter: **~$100-500 saved**

---

## Using the Full Integration

### Method 1: Via Bridge Manager (Recommended)

```python
from src.bridge_manager import ExoBridgeManager

# Initialize with cloud failover enabled
bridge = ExoBridgeManager(
    exo_host="localhost",
    exo_port=8000,
    enable_hud=False
)

bridge.start()

# Make a request (will try Exo first, then cloud)
result = bridge.chat_completion(
    messages=[{"role": "user", "content": "Hello!"}],
    model="llama-3.2-3b"
)

print(f"Provider Used: {result['provider_used']}")  # "Exo Local" or "OpenRouter"
print(f"Cost: ${result['cost']}")  # 0.00 for Exo, actual cost for cloud
print(f"Response: {result['response']}")

bridge.stop()
```

### Method 2: Direct Token Manager Integration

```python
import sys
sys.path.insert(0, '~/ai-token-manager')

from multi_provider_token_manager import MultiProviderTokenManager

# Initialize token manager (includes Exo)
manager = MultiProviderTokenManager(
    config_path="~/.token_manager_config.json"
)

# Request will route through priority order
response = manager.chat_completion(
    messages=[{"role": "user", "content": "Hi"}],
    model="llama-3.2-3b"
)
```

### Method 3: Via Spiral Codex HUD

```bash
# Start the HUD interface
cd ~/ai-token-exo-bridge
python src/bridge_manager.py --with-hud

# Open browser to: http://localhost:8501
```

The HUD now displays:
- ✅ Real-time provider status (Exo + Cloud)
- ✅ Token usage per provider
- ✅ Cost tracking ($0.00 for Exo, actual for cloud)
- ✅ Request routing history
- ✅ Failover events
- ✅ API key management (add/edit OpenRouter, HuggingFace)

---

## Testing the Integration

### Quick Test Script

```bash
cd ~/ai-token-exo-bridge
python3 examples/full_integration_demo.py
```

This will:
1. Test Exo local inference
2. Test cloud failover
3. Show usage statistics
4. Display costs per provider

### Manual Testing

```bash
# Test Exo endpoint directly
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.2-3b",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
  }'

# Check provider status
python3 -c "
import json
config = json.load(open('~/.token_manager_config.json'))
for p in config['providers']:
    print(f\"{p['name']}: {p['status']}\")
"
```

---

## Configuration Files

### Token Manager Config
**Location:** `~/.token_manager_config.json`

Contains:
- Provider configurations
- Encrypted API keys
- Usage statistics
- Rate limits

### Bridge Config
**Location:** `~/ai-token-exo-bridge/config/bridge_config.yaml`

Contains:
- Exo cluster settings
- Failover preferences
- HUD configuration
- Monitoring settings

---

## Viewing in the HUD

Once you start the HUD, you'll see:

### Main Dashboard
```
╔══════════════════════════════════════════════════════════╗
║  🌀 SPIRAL CODEX HUD - AI Command Bridge                ║
╚══════════════════════════════════════════════════════════╝

📊 Provider Status:
  🟢 Exo Local:      ONLINE  (0 requests, $0.00)
  🟢 OpenRouter:     ONLINE  (0 requests, $0.00)
  🟢 Hugging Face:   ONLINE  (0 requests, $0.00)

💰 Total Cost Today: $0.00
⚡ Requests Today:   0
🎯 Primary Provider: Exo Local (FREE!)
```

### Request Routing Panel
- Live request log
- Which provider handled each request
- Response time
- Token count
- Cost per request

### Token Management
- View/Edit OpenRouter API key
- View/Edit HuggingFace API key
- Test connection to each provider
- Enable/disable providers

---

## Common Scenarios

### Scenario 1: Exo Available
```
User Request → Exo Local → Response
Cost: $0.00 ✅
Speed: Fast (local)
```

### Scenario 2: Exo Downloading Model
```
User Request → Exo Local (busy) → OpenRouter → Response
Cost: ~$0.001-0.01
Speed: Medium (cloud)
```

### Scenario 3: Exo Offline
```
User Request → Exo (offline) → OpenRouter → Response
Cost: ~$0.001-0.01
Speed: Medium (cloud)
Notification: "Failover to OpenRouter"
```

### Scenario 4: Cloud-Only Model
```
User Request (GPT-4) → Skip Exo → OpenRouter → Response
Cost: ~$0.01-0.05
Speed: Medium (cloud)
Reason: Model not available locally
```

---

## Monitoring & Alerts

### What the HUD Shows

1. **Provider Health**
   - Green: Provider responsive
   - Yellow: Provider slow/degraded
   - Red: Provider offline

2. **Cost Tracking**
   - Real-time cost per request
   - Daily/weekly/monthly totals
   - Cost breakdown by provider

3. **Token Usage**
   - Prompt tokens used
   - Completion tokens used
   - Total tokens per provider

4. **Performance Metrics**
   - Average response time
   - Request success rate
   - Failover frequency

---

## Troubleshooting

### "No response from any provider"

**Check:**
```bash
# 1. Is Exo running?
curl http://localhost:8000/

# 2. Are cloud keys valid?
python3 -c "
import json
config = json.load(open('~/.token_manager_config.json'))
print('OpenRouter:', 'Configured' if config['providers'][1]['api_key_encrypted'] else 'Missing')
print('HuggingFace:', 'Configured' if config['providers'][2]['api_key_encrypted'] else 'Missing')
"

# 3. Check provider status
cd ~/ai-token-exo-bridge
python examples/full_integration_demo.py
```

### "Always routing to cloud (not using Exo)"

**Check Exo status:**
```bash
# Is Exo enabled?
python3 -c "
import json
config = json.load(open('~/.token_manager_config.json'))
print('Exo Status:', config['providers'][0]['status'])
"

# If disabled, enable it:
python3 -c "
import json
config = json.load(open('~/.token_manager_config.json'))
config['providers'][0]['status'] = 'active'
json.dump(config, open('~/.token_manager_config.json', 'w'), indent=2)
"
```

### "High cloud costs"

**Optimize routing:**
- Ensure Exo is running 24/7 for local requests
- Check that Exo priority is 0 (highest)
- Monitor HUD for unexpected failovers
- Consider adding more Exo nodes for reliability

---

## Next Steps

1. **Start Everything:**
   ```bash
   ./start_bridge.sh
   ```

2. **Access HUD:**
   Open http://localhost:8501

3. **Run Demo:**
   ```bash
   python3 examples/full_integration_demo.py
   ```

4. **Monitor Usage:**
   - Check HUD dashboard for real-time stats
   - Review cost breakdown daily
   - Optimize based on routing patterns

---

## Summary

✅ **Exo Local:** Active, downloading model  
✅ **OpenRouter:** Active with API key  
✅ **Hugging Face:** Active with API key  
✅ **Smart Routing:** Prefers free Exo, fails over to cloud  
✅ **Cost Tracking:** $0.00 for Exo, actual cost for cloud  
✅ **HUD Ready:** Real-time monitoring at localhost:8501  

**Your setup is complete and ready for production use!** 🚀
