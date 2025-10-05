# 🔒 Localhost Security Lockdown Guide

## ✅ Overview

This guide configures your Spiral Codex HUD to run in **strict localhost-only mode**, preventing any external network access.

---

## 🎯 What Gets Locked Down

### Services Restricted to 127.0.0.1
- ✅ Streamlit HUD (port 8501)
- ✅ Exo cluster endpoints (port 8000)
- ✅ API endpoints
- ✅ All provider routing
- ✅ Internal services

### Security Features Enabled
- 🔒 Bind to `127.0.0.1` only (no `0.0.0.0`)
- 🔒 Block external network interfaces
- 🔒 Disable CORS (no cross-origin)
- 🔒 Enable XSRF protection
- 🔒 Force localhost headers
- 🔒 Block port forwarding effectiveness

---

## 🚀 Enable Localhost Lockdown (ONE COMMAND)

Run this to lock everything to localhost:

```bash
cd /Users/dadhoosband/ai-token-exo-bridge
./restart_secure_localhost.sh
```

**This will:**
1. Stop all existing services
2. Apply localhost-only configuration
3. Lock all providers to 127.0.0.1
4. Start Streamlit bound to localhost only
5. Enable security protections

---

## ✅ What You Get

### Before Lockdown
```
Streamlit: http://0.0.0.0:8501 (accessible from network)
Exo: http://0.0.0.0:8000 (accessible from network)
Security: ⚠️ Network exposed
```

### After Lockdown
```
Streamlit: http://127.0.0.1:8501 (localhost ONLY)
Exo: http://127.0.0.1:8000 (localhost ONLY)
Security: ✅ Fully locked down
```

---

## 🔒 Security Guarantees

**What's Blocked:**
- ❌ Remote access from other machines
- ❌ Network interface binding (eth0, wifi, etc.)
- ❌ Port forwarding (ineffective)
- ❌ SSH tunneling to service
- ❌ Cross-origin requests (CORS disabled)
- ❌ External API access to your services

**What's Allowed:**
- ✅ Local browser on same machine
- ✅ `http://127.0.0.1:8501` access
- ✅ `http://localhost:8501` access
- ✅ Same-machine applications
- ✅ Command-line tools on same machine

---

## 🧪 Verify Lockdown Status

### Check Configuration
```bash
python3 enable_localhost_lockdown.py --status
```

Expected output:
```
Localhost Only: ✅ ENABLED
Bind Address: 127.0.0.1
External Access: 🔒 BLOCKED

Provider Security:
  Exo Local: ✅ LOCKED
    URL: http://127.0.0.1:8000
    Bind: 127.0.0.1
```

### Test External Access (Should Fail)
From another machine on your network:
```bash
# This should FAIL with connection refused
curl http://YOUR_MACHINE_IP:8501

# This should TIMEOUT
telnet YOUR_MACHINE_IP 8501
```

### Test Local Access (Should Work)
On your local machine:
```bash
# This should WORK
curl http://127.0.0.1:8501

# This should WORK
curl http://localhost:8501
```

---

## 📋 Configuration Details

### Streamlit Launch Parameters
```bash
streamlit run src/spiral_codex_hud.py \
    --server.port 8501 \
    --server.address 127.0.0.1          # Localhost only
    --server.headless true \
    --browser.serverAddress 127.0.0.1   # Force localhost
    --server.enableCORS false \         # Block cross-origin
    --server.enableXsrfProtection true  # XSRF protection
```

### Config File Settings
```json
{
  "security": {
    "localhost_only": true,
    "bind_address": "127.0.0.1",
    "allow_external": false,
    "enforce_local_access": true,
    "lockdown_enabled": true
  },
  "providers": [
    {
      "name": "Exo Local",
      "base_url": "http://127.0.0.1:8000",
      "bind_address": "127.0.0.1",
      "localhost_only": true,
      "allow_external": false
    }
  ]
}
```

---

## 🔧 Usage After Lockdown

### Starting Services
```bash
# Secure restart (applies lockdown)
./restart_secure_localhost.sh
```

### Accessing Dashboard
```bash
# Open browser on local machine
open http://127.0.0.1:8501

# Or use localhost
open http://localhost:8501
```

### Checking Logs
```bash
tail -f /tmp/spiral_codex_hud_secure.log
```

### Stopping Services
```bash
pkill -f "streamlit run"
```

---

## ⚠️ Important Notes

### Network Access
- **Will NOT work:** Accessing from another computer
- **Will NOT work:** Mobile devices on your network
- **Will NOT work:** Remote desktop to the service
- **WILL work:** Browser on the same machine
- **WILL work:** Command-line tools on same machine

### Port Forwarding
Even if you set up port forwarding on your router, services bound to `127.0.0.1` will NOT be accessible externally.

### SSH Tunneling
SSH tunnels can still work for YOU to access your own machine:
```bash
# From remote machine, tunnel to your localhost
ssh -L 8501:127.0.0.1:8501 user@your-machine

# Then access on remote machine
open http://localhost:8501
```

This is secure because:
- Only YOU with SSH credentials can create tunnel
- Traffic encrypted through SSH
- No direct network exposure

---

## 🆘 Troubleshooting

### Issue: Can't Access from Local Browser

**Check:**
```bash
# Verify service is running
ps aux | grep streamlit

# Check bind address
netstat -an | grep 8501

# Should show: 127.0.0.1:8501 (not 0.0.0.0:8501)
```

**Fix:**
```bash
./restart_secure_localhost.sh
```

### Issue: Getting CORS Errors

**This is expected and correct!** CORS is disabled for security.

**Solution:**
- Access only through `http://127.0.0.1:8501`
- Don't use external domain names
- Don't embed in iframes from other domains

### Issue: Want to Disable Lockdown

**To allow network access again:**
1. Edit `restart_secure_localhost.sh`
2. Change `--server.address 127.0.0.1` to `--server.address 0.0.0.0`
3. Change `--server.enableCORS false` to `--server.enableCORS true`
4. Restart services

**WARNING:** This exposes your services to network access!

---

## 🎯 Security Best Practices

### ✅ DO
- Keep lockdown enabled for normal use
- Access only from local browser
- Use SSH tunnels for remote access
- Monitor logs regularly
- Keep API keys secure in config

### ❌ DON'T
- Disable lockdown unless absolutely necessary
- Bind to `0.0.0.0` in production
- Share your machine's network address
- Expose services to internet
- Disable XSRF protection

---

## 📊 Security Comparison

| Feature | Without Lockdown | With Lockdown |
|---------|------------------|---------------|
| **Network Access** | ⚠️ Anyone on network | ✅ Localhost only |
| **Port Forwarding** | ⚠️ Exposes service | ✅ Ineffective |
| **CORS** | ⚠️ Enabled | ✅ Disabled |
| **Bind Address** | ⚠️ 0.0.0.0 (all) | ✅ 127.0.0.1 (localhost) |
| **Remote Access** | ⚠️ Possible | ✅ Blocked |
| **API Keys** | ⚠️ Network exposed | ✅ Local only |
| **XSRF Protection** | ⚠️ Optional | ✅ Enabled |

---

## 🚀 Quick Commands

### Enable Lockdown
```bash
./restart_secure_localhost.sh
```

### Check Status
```bash
python3 enable_localhost_lockdown.py --status
```

### View Logs
```bash
tail -f /tmp/spiral_codex_hud_secure.log
```

### Test Local Access
```bash
curl http://127.0.0.1:8501
```

### Stop Services
```bash
pkill -f "streamlit run"
```

---

## ✅ Verification Checklist

After enabling lockdown, verify:

- [ ] Streamlit running on 127.0.0.1:8501
- [ ] Local browser access works
- [ ] External access blocked (test from another device)
- [ ] CORS disabled
- [ ] XSRF protection enabled
- [ ] Config shows `localhost_only: true`
- [ ] All providers locked to localhost
- [ ] No `0.0.0.0` bindings

---

## 🎓 Summary

**Your system is now locked to localhost-only access:**

✅ Streamlit: `http://127.0.0.1:8501` only  
✅ All services: Bound to localhost  
✅ External access: BLOCKED  
✅ CORS: Disabled  
✅ XSRF: Enabled  
✅ API keys: Protected on local machine only  

**Security level: Maximum for local development**

---

## 📚 Related Documentation

- **SYSTEM_READY.md** - System setup guide
- **FREE_MODELS_ONLY_GUIDE.md** - Free models usage
- **OPENROUTER_ONLY_GUIDE.md** - OpenRouter configuration
- **PHD_LEVEL_ENHANCEMENTS.md** - Technical architecture

---

**Your system is now locked down to localhost-only access. No external network exposure!** 🔒✨

*Last updated: October 5, 2025*
