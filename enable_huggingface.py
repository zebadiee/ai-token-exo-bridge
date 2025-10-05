#!/usr/bin/env python3
"""
Re-enable HuggingFace Provider

This script re-enables HuggingFace with a new, valid API token.
Use this when you've generated a fresh token with correct permissions.

Usage:
    python enable_huggingface.py YOUR_NEW_HF_TOKEN
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import shutil

CONFIG_PATH = Path.home() / ".token_manager_config.json"
BACKUP_PATH = Path.home() / f".token_manager_config.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"


def enable_huggingface(new_token: str):
    """
    Re-enable HuggingFace with a new API token
    
    Args:
        new_token: New HuggingFace API token with correct permissions
        
    Returns:
        bool: True if successful
    """
    print("=" * 70)
    print("RE-ENABLING HUGGINGFACE WITH NEW TOKEN")
    print("=" * 70)
    print()
    
    # Validate token format
    if not new_token.startswith('hf_'):
        print("⚠️  Warning: HuggingFace tokens typically start with 'hf_'")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            return False
    
    # Check if config exists
    if not CONFIG_PATH.exists():
        print(f"❌ Config file not found: {CONFIG_PATH}")
        return False
    
    # Backup config
    print(f"📦 Creating backup: {BACKUP_PATH}")
    shutil.copy2(CONFIG_PATH, BACKUP_PATH)
    print(f"✅ Backup created")
    print()
    
    # Load config
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False
    
    # Update HuggingFace provider
    print("🔧 Updating HuggingFace Configuration...")
    print("-" * 70)
    
    hf_found = False
    providers = config.get('providers', [])
    
    for provider in providers:
        name = provider.get('name', '')
        
        if 'hugging' in name.lower() or name == 'Hugging Face':
            # Update token and status
            provider['api_key'] = new_token
            provider['status'] = 'active'
            
            # Remove disabled markers
            provider.pop('disabled_reason', None)
            provider.pop('disabled_at', None)
            
            # Update timestamp
            provider['updated_at'] = datetime.now().isoformat()
            
            # Reset usage stats
            if 'usage' in provider:
                provider['usage']['last_reset'] = datetime.now().isoformat()
            
            hf_found = True
            print(f"  ✓ HuggingFace: inactive → active (enabled)")
            print(f"  ✓ API Token: Updated (starts with {new_token[:6]}...)")
            print()
    
    if not hf_found:
        print("❌ HuggingFace provider not found in config")
        return False
    
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
    
    # Show updated status
    print("📊 Updated Provider Status:")
    print("-" * 70)
    for provider in providers:
        name = provider.get('name', 'Unknown')
        status = provider.get('status', 'unknown')
        status_icon = "✅" if status == 'active' else "⚠️"
        print(f"  {status_icon} {name:20s} Status: {status}")
    
    print()
    print("=" * 70)
    print("HUGGINGFACE RE-ENABLED")
    print("=" * 70)
    print()
    print("Next Steps:")
    print("  1. Restart Spiral Codex HUD (Ctrl+C, then rerun)")
    print("  2. Verify HuggingFace shows as 'HEALTHY' in dashboard")
    print("  3. Test inference with a HuggingFace model")
    print()
    print("If you still get 401/403 errors:")
    print("  - Verify token has 'Make calls to Inference Providers' permission")
    print("  - Check account email is verified")
    print("  - Some models may require billing info on file")
    print("  - Run diagnostic: python src/huggingface_diagnostic.py YOUR_TOKEN")
    print()
    print(f"Backup saved to: {BACKUP_PATH}")
    print()
    
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("=" * 70)
        print("RE-ENABLE HUGGINGFACE")
        print("=" * 70)
        print()
        print("Usage:")
        print("  python enable_huggingface.py YOUR_NEW_HF_TOKEN")
        print()
        print("Example:")
        print("  python enable_huggingface.py hf_abcdefghijklmnop")
        print()
        print("Get a new token:")
        print("  1. Go to: https://huggingface.co/settings/tokens")
        print("  2. Create new token")
        print("  3. Enable 'Make calls to Inference Providers' permission")
        print("  4. Copy token and run this script")
        print()
        sys.exit(1)
    
    new_token = sys.argv[1].strip()
    success = enable_huggingface(new_token)
    sys.exit(0 if success else 1)
