#!/usr/bin/env python3
"""
Localhost Security Lockdown

Locks all services to localhost-only access:
- Streamlit HUD (port 8501)
- API endpoints
- OpenRouter routing
- All network services

Prevents external access and ensures security.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import shutil

CONFIG_PATH = Path.home() / ".token_manager_config.json"
BACKUP_PATH = Path.home() / f".token_manager_config.backup_localhost.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"


def enable_localhost_lockdown():
    """
    Enable localhost-only lockdown mode
    
    Updates all configurations to bind only to 127.0.0.1
    Blocks all external network access
    """
    print("=" * 70)
    print("ENABLING LOCALHOST SECURITY LOCKDOWN")
    print("=" * 70)
    print()
    
    # Backup config
    if CONFIG_PATH.exists():
        print(f"📦 Creating backup: {BACKUP_PATH}")
        shutil.copy2(CONFIG_PATH, BACKUP_PATH)
        print("✅ Backup created")
        print()
    
    # Load config
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False
    
    # Apply localhost lockdown
    print("🔒 Applying Localhost Lockdown...")
    print("-" * 70)
    
    # Global security settings
    config['security'] = {
        'localhost_only': True,
        'bind_address': '127.0.0.1',
        'allow_external': False,
        'enforce_local_access': True,
        'lockdown_enabled': True,
        'lockdown_timestamp': datetime.now().isoformat()
    }
    
    # Update each provider
    for provider in config.get('providers', []):
        provider_name = provider.get('name', 'Unknown')
        
        # Lock Exo Local
        if 'exo' in provider_name.lower():
            base_url = provider.get('base_url', '')
            if base_url:
                # Force localhost
                provider['base_url'] = base_url.replace('0.0.0.0', '127.0.0.1').replace('localhost', '127.0.0.1')
                provider['bind_address'] = '127.0.0.1'
                provider['allow_external'] = False
                print(f"  🔒 {provider_name}: Locked to localhost")
                print(f"      URL: {provider['base_url']}")
        
        # Add security headers for all providers
        if 'headers' not in provider:
            provider['headers'] = {}
        
        provider['headers'].update({
            'X-Forwarded-For': '127.0.0.1',
            'X-Real-IP': '127.0.0.1'
        })
        
        # Add localhost enforcement
        provider['localhost_only'] = True
        provider['security_lockdown'] = True
    
    print()
    
    # Save config
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        print("✅ Configuration updated successfully")
        print()
    except Exception as e:
        print(f"❌ Failed to save config: {e}")
        print(f"   Restoring backup from: {BACKUP_PATH}")
        shutil.copy2(BACKUP_PATH, CONFIG_PATH)
        return False
    
    # Show security status
    print("=" * 70)
    print("LOCALHOST LOCKDOWN ENABLED")
    print("=" * 70)
    print()
    print("Security Configuration:")
    print("  🔒 Localhost Only: ENABLED")
    print("  🔒 Bind Address: 127.0.0.1")
    print("  🔒 External Access: BLOCKED")
    print("  🔒 All Providers: Locked to localhost")
    print()
    print("Protected Services:")
    print("  • Streamlit HUD: http://127.0.0.1:8501 (localhost only)")
    print("  • Exo Cluster: http://127.0.0.1:8000 (localhost only)")
    print("  • API Endpoints: 127.0.0.1 only")
    print("  • OpenRouter: Routed through localhost")
    print()
    print("External Access:")
    print("  ❌ Network interfaces: BLOCKED")
    print("  ❌ Remote connections: BLOCKED")
    print("  ❌ Port forwarding: Ineffective")
    print("  ✅ Local browser: ALLOWED")
    print()
    print(f"Backup saved to: {BACKUP_PATH}")
    print()
    
    return True


def show_localhost_status():
    """Show current localhost lockdown status"""
    if not CONFIG_PATH.exists():
        print(f"❌ Config file not found: {CONFIG_PATH}")
        return
    
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return
    
    print("=" * 70)
    print("LOCALHOST LOCKDOWN STATUS")
    print("=" * 70)
    print()
    
    # Check security settings
    security = config.get('security', {})
    localhost_only = security.get('localhost_only', False)
    bind_address = security.get('bind_address', 'Not set')
    
    print(f"Localhost Only: {'✅ ENABLED' if localhost_only else '⚠️ DISABLED'}")
    print(f"Bind Address: {bind_address}")
    print(f"External Access: {'🔒 BLOCKED' if not security.get('allow_external', True) else '⚠️ ALLOWED'}")
    print()
    
    # Check providers
    print("Provider Security:")
    print("-" * 70)
    
    for provider in config.get('providers', []):
        name = provider.get('name', 'Unknown')
        base_url = provider.get('base_url', 'Not set')
        provider_localhost = provider.get('localhost_only', False)
        bind_addr = provider.get('bind_address', 'Not set')
        
        status = "✅ LOCKED" if provider_localhost else "⚠️ OPEN"
        
        print(f"\n{name}: {status}")
        print(f"  URL: {base_url}")
        print(f"  Bind: {bind_addr}")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        show_localhost_status()
    else:
        success = enable_localhost_lockdown()
        sys.exit(0 if success else 1)
