# 🆓 Free Models Only Guide - Zero Cost Operation

## ✅ Configuration Complete

Your Spiral Codex HUD is now configured to use **ONLY FREE (zero-cost) models from OpenRouter**.

**No accidental charges possible!**

---

## 🎯 What This Means

| Feature | Status | Protection |
|---------|--------|------------|
| **Free Models Only** | ✅ ENABLED | Only $0.00 models shown |
| **Paid Models** | 🚫 BLOCKED | Cannot be selected or used |
| **Max Cost Per Request** | $0.00 | Hard limit enforced |
| **Billing Protection** | ✅ ACTIVE | No charges possible |
| **Model Cache** | 24 hours | Auto-refreshes free list |

---

## 🚀 How It Works

### 1. **Model Filtering**
- System fetches all OpenRouter models
- Filters for pricing: `prompt_cost == $0.00 AND completion_cost == $0.00`
- **Only** shows models with zero cost in UI

### 2. **Dual-Layer Protection**
- **UI Layer**: Only free models appear in dropdown
- **Backend Layer**: Blocks any paid model request (even if manually crafted)

### 3. **Auto-Refresh**
- Free model list cached for 24 hours
- Auto-refreshes to catch new free models
- Always current with OpenRouter's offerings

---

## 📋 Free Models Available

Your system will show models like:

**Common Free Models (Examples):**
- `google/gemini-flash-1.5` (FREE)
- `meta-llama/llama-3-8b-instruct` (FREE)
- `mistralai/mistral-7b-instruct` (FREE)
- Plus many more zero-cost options!

**Note:** Actual list varies based on OpenRouter's current free tier offerings.

---

## 🔧 Usage Instructions

### Step 1: Check Free Models
```bash
# View current free models configuration
python enable_free_models_only.py --status

# Test free models filter (shows available free models)
cd /Users/dadhoosband/ai-token-exo-bridge
cat ~/.token_manager_config.json | grep -A5 "free_models_only"
```

### Step 2: Restart System
```bash
cd /Users/dadhoosband/ai-token-exo-bridge
./restart_openrouter_only.sh
```

### Step 3: Use Free Models
1. Open http://localhost:8501
2. Go to model selection
3. **Only free models will be shown**
4. Select any model - all are $0.00
5. Run inference with zero billing risk

---

## ✅ What You Get

**Free Models Features:**
- ✅ **Zero Cost** - All models are $0.00
- ✅ **Validated** - Only working free models shown
- ✅ **Safe** - No hidden charges or surprises
- ✅ **Curated** - System filters daily for free options
- ✅ **Context Lengths** - Varies by model (typically 4K-32K tokens)

**Typical Free Model Count:**
- 5-15 free models typically available
- Varies based on OpenRouter promotions
- Refreshed automatically every 24 hours

---

## 🛡️ Protection Layers

Your system has **3 layers of billing protection**:

### Layer 1: Configuration
```json
{
  "free_models_only": true,
  "max_cost_per_request": 0.0,
  "billing_protection": {
    "enabled": true,
    "block_paid_models": true
  }
}
```

### Layer 2: Model Filtering
- API fetches all models
- Filters: `cost == $0.00`
- Only free models cached
- UI shows filtered list only

### Layer 3: Request Validation
- Before sending request
- Validates model is in free list
- Blocks if paid model attempted
- Returns error to user

---

## 📊 Expected Dashboard View

```
OpenRouter Free Models Status:
✅ Free Models Available: 7-15 models
✅ Cost Per Request: $0.00 (guaranteed)
✅ Billing Protection: ACTIVE
✅ Last Model Refresh: [timestamp]

Available Models:
  • google/gemini-flash-1.5 (FREE - 32K tokens)
  • meta-llama/llama-3-8b-instruct (FREE - 8K tokens)
  • mistralai/mistral-7b-instruct (FREE - 8K tokens)
  [... more free models ...]

Total Cost Today: $0.00
Total Cost This Month: $0.00
```

---

## 🔄 Model List Refresh

### Automatic Refresh
- Cache TTL: 24 hours
- Auto-fetches on expiry
- Updates free model list
- Seamless operation

### Manual Refresh
```bash
# Force refresh free models list
cd /Users/dadhoosband/ai-token-exo-bridge/src
python openrouter_free_models.py YOUR_OPENROUTER_KEY
```

### In Dashboard
- Go to "Providers" tab
- Click "Refresh Free Models" button
- Updates list immediately

---

## 🧪 Testing Your Configuration

### Test 1: Verify Free Models Only
```bash
python enable_free_models_only.py --status
```

Expected output:
```
Free Models Only: ✅ ENABLED
Max Cost Per Request: $0.0
Billing Protection: ✅ ENABLED
```

### Test 2: View Available Free Models
```bash
cd /Users/dadhoosband/ai-token-exo-bridge
# Get your OpenRouter key from config
OPENROUTER_KEY=$(cat ~/.token_manager_config.json | grep -A1 "OpenRouter" | grep "api_key" | cut -d'"' -f4)

# List free models
python src/openrouter_free_models.py $OPENROUTER_KEY
```

### Test 3: Test in Dashboard
1. Open http://localhost:8501
2. Go to model selection
3. Dropdown should show only models marked "(FREE)"
4. Hover over model - should show "$0.00 cost"
5. Select and test - no charges

---

## 🆘 Troubleshooting

### Issue: "No Free Models Available"

**Possible Causes:**
- API key invalid
- Internet connection issue
- OpenRouter temporarily has no free models

**Solutions:**
```bash
# 1. Verify API key
cat ~/.token_manager_config.json | grep -A3 "OpenRouter"

# 2. Test API connection
curl -H "Authorization: Bearer YOUR_KEY" \
  https://openrouter.ai/api/v1/models

# 3. Force refresh
python src/openrouter_free_models.py YOUR_KEY
```

### Issue: "Seeing Paid Models in UI"

**Solution:**
```bash
# Re-enable free-only mode
python enable_free_models_only.py

# Restart system
./restart_openrouter_only.sh

# Verify
python enable_free_models_only.py --status
```

### Issue: "Model Pricing Changed"

**Solution:**
- Free models list auto-refreshes every 24 hours
- If a model becomes paid, it's removed on next refresh
- Force refresh: `python src/openrouter_free_models.py YOUR_KEY`

---

## 💡 Understanding Free Tier

### What Makes a Model "Free"?
- **Prompt Cost:** $0.00 per 1K tokens
- **Completion Cost:** $0.00 per 1K tokens
- **Both must be zero** to qualify

### Free Model Characteristics
- Typically smaller models (7B-13B parameters)
- Good for testing and development
- Suitable for many production use cases
- Lower rate limits than paid models

### When to Consider Paid Models
- Need for largest/newest models (GPT-4, Claude Opus)
- Higher rate limits required
- Specialized capabilities
- Production at scale

**For now:** You're safely using free models with zero risk!

---

## 📚 Scripts Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `enable_free_models_only.py` | Enable free-only mode | `python enable_free_models_only.py` |
| `enable_free_models_only.py --status` | Check current status | `python enable_free_models_only.py --status` |
| `src/openrouter_free_models.py` | List free models | `python src/openrouter_free_models.py API_KEY` |
| `restart_openrouter_only.sh` | Restart system | `./restart_openrouter_only.sh` |

---

## 🎯 Quick Reference

### Enable Free-Only Mode
```bash
python enable_free_models_only.py
./restart_openrouter_only.sh
```

### Check Status
```bash
python enable_free_models_only.py --status
```

### List Available Free Models
```bash
# Extract API key from config
OPENROUTER_KEY=$(cat ~/.token_manager_config.json | python3 -c "import json, sys; print(json.load(sys.stdin)['providers'][1]['api_key'])")

# List free models
python src/openrouter_free_models.py $OPENROUTER_KEY
```

### View Configuration
```bash
cat ~/.token_manager_config.json | grep -A10 "free_models_only"
```

---

## ✅ Summary

Your Spiral Codex HUD is now configured for **100% free operation**:

- ✅ **Only free models shown** in UI
- ✅ **Paid models blocked** at multiple layers
- ✅ **Zero billing risk** guaranteed
- ✅ **Auto-refreshing** free model list
- ✅ **Production-ready** with zero cost

**You can use your system without any fear of charges!**

---

## 🚀 Next Steps

1. **Restart your system:**
   ```bash
   cd /Users/dadhoosband/ai-token-exo-bridge
   ./restart_openrouter_only.sh
   ```

2. **Open dashboard:** http://localhost:8501

3. **Select free model** from dropdown (all shown are $0.00)

4. **Start using** with zero billing risk!

---

## 📖 Related Documentation

- **OPENROUTER_ONLY_GUIDE.md** - OpenRouter-only operation
- **SYSTEM_READY.md** - System ready guide
- **PHD_LEVEL_ENHANCEMENTS.md** - Technical architecture

---

**Your system is now configured for free-only operation. No charges possible!** 🆓✨

*Last updated: October 5, 2025*
