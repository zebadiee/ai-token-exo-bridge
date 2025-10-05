#!/usr/bin/env python3
"""
Disable HuggingFace Provider - OpenRouter Only Configuration

This script safely disables HuggingFace while keeping OpenRouter active.
It updates the token manager configuration to exclude HuggingFace from
all operations until you're ready to re-enable it with a valid token.
"""

import json
from pathlib import Path
from datetime import datetime
import shutil

CONFIG_PATH = Path.home() / ".token_manager_config.json"
BACKUP_PATH = Path.home() / f".token_manager_config.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"


def disable_huggingface():
    """
    Disable HuggingFace provider while keeping OpenRouter active
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("=" * 70)
    print("DISABLING HUGGINGFACE - OPENROUTER ONLY MODE")
    print("=" * 70)
    print()
    
    # Check if config exists
    if not CONFIG_PATH.exists():
        print(f"❌ Config file not found: {CONFIG_PATH}")
        return False
    
    # Backup original config
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
    
    # Show current provider status
    print("📊 Current Provider Status:")
    print("-" * 70)
    providers = config.get('providers', [])
    for provider in providers:
        name = provider.get('name', 'Unknown')
        status = provider.get('status', 'unknown')
        has_key = bool(provider.get('api_key', ''))
        print(f"  • {name:20s} Status: {status:10s} Has Key: {has_key}")
    print()
    
    # Disable HuggingFace
    print("🔧 Updating Configuration...")
    print("-" * 70)
    
    hf_found = False
    openrouter_found = False
    
    for provider in providers:
        name = provider.get('name', '')
        
        if 'hugging' in name.lower() or name == 'Hugging Face':
            # Disable HuggingFace
            old_status = provider.get('status', 'unknown')
            provider['status'] = 'inactive'
            provider['disabled_reason'] = 'Temporarily disabled - HTTP 401/403 errors'
            provider['disabled_at'] = datetime.now().isoformat()
            hf_found = True
            print(f"  ✓ HuggingFace: {old_status} → inactive (disabled)")
        
        elif 'openrouter' in name.lower() or name == 'OpenRouter':
            # Ensure OpenRouter is active
            old_status = provider.get('status', 'unknown')
            if provider.get('api_key'):
                provider['status'] = 'active'
                openrouter_found = True
                print(f"  ✓ OpenRouter: {old_status} → active (enabled)")
            else:
                print(f"  ⚠ OpenRouter: No API key found - cannot activate")
        
        elif 'exo' in name.lower():
            # Keep Exo as is
            status = provider.get('status', 'unknown')
            print(f"  ℹ Exo: {status} (unchanged)")
    
    print()
    
    if not hf_found:
        print("⚠️  HuggingFace provider not found in config")
    
    if not openrouter_found:
        print("⚠️  OpenRouter provider not found or has no API key")
        print("    Please add your OpenRouter API key to use the system")
    
    # Save updated config
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
    
    # Show new status
    print("📊 Updated Provider Status:")
    print("-" * 70)
    for provider in providers:
        name = provider.get('name', 'Unknown')
        status = provider.get('status', 'unknown')
        provider_type = provider.get('type', 'unknown')
        
        status_icon = "✅" if status == 'active' else "⚠️" if status == 'inactive' else "❓"
        print(f"  {status_icon} {name:20s} Status: {status:10s} Type: {provider_type}")
    
    print()
    print("=" * 70)
    print("CONFIGURATION UPDATE COMPLETE")
    print("=" * 70)
    print()
    print("Next Steps:")
    print("  1. Restart Spiral Codex HUD (Ctrl+C in terminal, then rerun)")
    print("  2. Verify OpenRouter shows as 'HEALTHY' in dashboard")
    print("  3. Use OpenRouter for all inference requests")
    print("  4. When ready to re-enable HuggingFace:")
    print("     - Generate new HF token with correct permissions")
    print("     - Run: python enable_huggingface.py YOUR_NEW_TOKEN")
    print()
    print(f"Backup saved to: {BACKUP_PATH}")
    print()
    
    return True


def show_status():
    """Show current provider status without making changes"""
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
    print("CURRENT PROVIDER STATUS")
    print("=" * 70)
    print()
    
    providers = config.get('providers', [])
    
    for provider in providers:
        name = provider.get('name', 'Unknown')
        status = provider.get('status', 'unknown')
        provider_type = provider.get('type', 'unknown')
        has_key = bool(provider.get('api_key', ''))
        
        status_icon = "✅" if status == 'active' else "⚠️" if status == 'inactive' else "❓"
        
        print(f"{status_icon} {name}")
        print(f"   Status: {status}")
        print(f"   Type: {provider_type}")
        print(f"   Has API Key: {has_key}")
        
        if 'disabled_reason' in provider:
            print(f"   Disabled Reason: {provider['disabled_reason']}")
        if 'disabled_at' in provider:
            print(f"   Disabled At: {provider['disabled_at']}")
        
        print()
    
    print("=" * 70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        show_status()
    else:
        success = disable_huggingface()
        sys.exit(0 if success else 1)
