# 🎯 OpenRouter-Only Quick Start Guide

## ✅ Configuration Complete

HuggingFace has been **temporarily disabled** to eliminate the persistent HTTP 401/403 errors.

Your system is now configured to run **reliably with OpenRouter only**.

---

## 📊 Current Provider Status

| Provider | Status | Action |
|----------|--------|--------|
| **OpenRouter** | ✅ ACTIVE | Primary provider - 326 models available |
| **HuggingFace** | ⚠️ INACTIVE | Temporarily disabled (401/403 errors) |
| **Exo Local** | ℹ️ DISABLED | Can be enabled if needed |

---

## 🚀 Restart Your System

### Option 1: Automated Restart (Recommended)
```bash
cd /Users/dadhoosband/ai-token-exo-bridge
./restart_openrouter_only.sh
```

This script will:
1. Stop the existing Streamlit process
2. Show current provider configuration
3. Start fresh with HuggingFace disabled
4. Confirm OpenRouter is healthy

### Option 2: Manual Restart
```bash
# Stop existing process
pkill -f "streamlit run src/spiral_codex_hud.py"

# Start fresh
cd /Users/dadhoosband/ai-token-exo-bridge
streamlit run src/spiral_codex_hud.py --server.port 8501
```

---

## 🎯 Using OpenRouter-Only Mode

### In the Spiral Codex HUD

1. **Open Dashboard**: http://localhost:8501

2. **Verify Provider Status**:
   - Go to **"Providers"** or **"System Status"** tab
   - Confirm **OpenRouter** shows as **"HEALTHY"**
   - HuggingFace should show as **"INACTIVE"** or **"OFFLINE"** (ignore it)

3. **Select Models**:
   - Model dropdown will show **only OpenRouter models**
   - 326 validated models available
   - No ghost models or unavailable selections

4. **Run Inference**:
   - All requests automatically route to OpenRouter
   - Self-healing still active for OpenRouter
   - Exo can be used as fallback if enabled

---

## 🔧 System Behavior

### ✅ What Works
- All OpenRouter models (claude, gpt, llama, etc.)
- Model validation and preflight checks
- Self-healing for OpenRouter
- Token management
- Usage tracking
- Zero doomed requests (OpenRouter only)

### ⚠️ What's Disabled
- HuggingFace models (temporarily unavailable)
- HuggingFace health checks (will show offline)
- HuggingFace failover routing

### 🔄 Automatic Behavior
- System skips HuggingFace in all operations
- Only validated OpenRouter models shown
- Self-healing ignores HuggingFace
- No 401/403 errors logged

---

## 📈 Expected Dashboard View

```
Provider Health:
✅ OpenRouter       HEALTHY    326 models   0ms latency
⚠️  HuggingFace     INACTIVE   (disabled)   -
ℹ️  Exo Local       DISABLED   -            -

Active Models: 326 (OpenRouter only)
```

---

## 🔄 Re-enabling HuggingFace (When Ready)

### Step 1: Generate New HF Token
1. Go to: https://huggingface.co/settings/tokens
2. **Delete** old token
3. **Create new token**
4. Name it (e.g., "Spiral-Codex-Inference")
5. **Crucial**: Enable **"Make calls to Inference Providers"** permission
6. Also enable: "Read access to contents of all repos"
7. Copy the token

### Step 2: Re-enable in System
```bash
cd /Users/dadhoosband/ai-token-exo-bridge
python enable_huggingface.py hf_YOUR_NEW_TOKEN_HERE
```

### Step 3: Restart
```bash
./restart_openrouter_only.sh
```

### Step 4: Verify
- Dashboard should show HuggingFace as **HEALTHY**
- Both OpenRouter and HuggingFace available
- Full multi-provider operation restored

---

## 🧪 Testing Your Configuration

### Test 1: Provider Status
```bash
# View current provider status
python disable_huggingface.py --status
```

Expected output:
```
✅ OpenRouter - Status: active
⚠️  HuggingFace - Status: inactive (Disabled Reason: Temporarily disabled)
```

### Test 2: Access Dashboard
1. Open http://localhost:8501
2. Should load without errors
3. OpenRouter models visible
4. HuggingFace status shows as inactive/offline

### Test 3: Run Inference
1. Select any OpenRouter model
2. Enter prompt
3. Send request
4. Should complete successfully (0% doomed rate)

---

## 🆘 Troubleshooting

### Issue: "Still seeing HuggingFace errors"

**Solution:**
```bash
# Force restart with clean config
./restart_openrouter_only.sh
```

### Issue: "OpenRouter not showing as healthy"

**Check:**
1. API key is valid (check config: `cat ~/.token_manager_config.json`)
2. Internet connection active
3. OpenRouter service status: https://status.openrouter.ai

**Fix:**
```bash
# Verify OpenRouter key in config
cat ~/.token_manager_config.json | grep -A2 "OpenRouter"

# Should show: "status": "active" and api_key present
```

### Issue: "No models showing in dropdown"

**Solution:**
```bash
# Force model sync
# In HUD: Go to Providers tab → Click "Refresh Models"
# Or restart:
./restart_openrouter_only.sh
```

---

## 📚 Scripts Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `disable_huggingface.py` | Disable HuggingFace | `python disable_huggingface.py` |
| `enable_huggingface.py` | Re-enable HuggingFace | `python enable_huggingface.py TOKEN` |
| `restart_openrouter_only.sh` | Restart system | `./restart_openrouter_only.sh` |
| `disable_huggingface.py --status` | Check status | `python disable_huggingface.py --status` |

---

## ✅ Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| Main Config | Provider settings | `~/.token_manager_config.json` |
| Backup | Auto-created before changes | `~/.token_manager_config.backup.*.json` |
| Logs | Runtime logs | `/tmp/spiral_codex_hud.log` |

---

## 🎓 Summary

Your Spiral Codex HUD is now configured for **stable, OpenRouter-only operation**:

✅ HuggingFace disabled (no more 401/403 errors)  
✅ OpenRouter active (326 models available)  
✅ Zero doomed requests (OpenRouter validated)  
✅ Self-healing operational  
✅ Production-ready  

**You can now use the system reliably with OpenRouter while you resolve HuggingFace permissions at your convenience.**

---

## 🚀 Ready to Go!

Run this command to start:
```bash
cd /Users/dadhoosband/ai-token-exo-bridge
./restart_openrouter_only.sh
```

Then open: **http://localhost:8501**

---

*OpenRouter-Only Quick Start Guide*  
*For full documentation, see PHD_LEVEL_ENHANCEMENTS.md*
