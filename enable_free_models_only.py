#!/usr/bin/env python3
"""
Free Models Configuration Manager

Updates Spiral Codex HUD to use only free OpenRouter models.
Prevents accidental charges by filtering and enforcing free-only mode.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import shutil

CONFIG_PATH = Path.home() / ".token_manager_config.json"
BACKUP_PATH = Path.home() / f".token_manager_config.backup_free_mode.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"


def enable_free_models_only():
    """
    Enable free-models-only mode in configuration
    
    Updates config to:
    1. Add free_models_only flag
    2. Configure OpenRouter with cost restrictions
    3. Enable budget protection
    """
    print("=" * 70)
    print("ENABLING FREE MODELS ONLY MODE")
    print("=" * 70)
    print()
    
    # Check config exists
    if not CONFIG_PATH.exists():
        print(f"❌ Config file not found: {CONFIG_PATH}")
        return False
    
    # Backup config
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
    
    # Update configuration
    print("🔧 Enabling Free Models Only Mode...")
    print("-" * 70)
    
    # Add global free-models-only flag
    config['free_models_only'] = True
    config['max_cost_per_request'] = 0.0
    config['billing_protection'] = {
        'enabled': True,
        'max_daily_cost': 0.0,
        'alert_threshold': 0.0,
        'block_paid_models': True
    }
    
    # Update OpenRouter provider config
    for provider in config.get('providers', []):
        if 'openrouter' in provider.get('name', '').lower():
            provider['free_models_only'] = True
            provider['max_cost_per_request'] = 0.0
            provider['pricing_check'] = 'enforce'
            
            # Add model filtering config
            provider['model_filter'] = {
                'mode': 'free_only',
                'max_prompt_cost': 0.0,
                'max_completion_cost': 0.0,
                'cache_ttl_hours': 24
            }
            
            print(f"  ✓ OpenRouter: Free models only mode enabled")
            print(f"  ✓ Cost restrictions: $0.00 max per request")
            print(f"  ✓ Billing protection: Active")
    
    # Save updated config
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        print()
        print("✅ Configuration updated successfully")
        print()
    except Exception as e:
        print(f"❌ Failed to save config: {e}")
        print(f"   Restoring backup from: {BACKUP_PATH}")
        shutil.copy2(BACKUP_PATH, CONFIG_PATH)
        return False
    
    # Show summary
    print("=" * 70)
    print("FREE MODELS ONLY MODE ENABLED")
    print("=" * 70)
    print()
    print("Benefits:")
    print("  ✅ Only zero-cost models will be shown in UI")
    print("  ✅ Paid models automatically blocked")
    print("  ✅ No accidental charges possible")
    print("  ✅ Budget protection active")
    print()
    print("Configuration:")
    print("  • Max cost per request: $0.00")
    print("  • Max daily cost: $0.00")
    print("  • Paid models: BLOCKED")
    print("  • Free model cache: 24 hours")
    print()
    print("Next Steps:")
    print("  1. Restart Spiral Codex HUD")
    print("  2. Model dropdown will show only free models")
    print("  3. Use with zero billing risk")
    print()
    print(f"Backup saved to: {BACKUP_PATH}")
    print()
    
    return True


def show_free_models_status():
    """Show current free models configuration status"""
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
    print("FREE MODELS CONFIGURATION STATUS")
    print("=" * 70)
    print()
    
    # Check global settings
    free_only = config.get('free_models_only', False)
    max_cost = config.get('max_cost_per_request', 'Not set')
    billing = config.get('billing_protection', {})
    
    print(f"Free Models Only: {'✅ ENABLED' if free_only else '⚠️ DISABLED'}")
    print(f"Max Cost Per Request: ${max_cost}")
    print(f"Billing Protection: {'✅ ENABLED' if billing.get('enabled') else '⚠️ DISABLED'}")
    print()
    
    # Check provider settings
    print("Provider Settings:")
    print("-" * 70)
    
    for provider in config.get('providers', []):
        name = provider.get('name', 'Unknown')
        
        if 'openrouter' in name.lower():
            provider_free_only = provider.get('free_models_only', False)
            provider_max_cost = provider.get('max_cost_per_request', 'Not set')
            model_filter = provider.get('model_filter', {})
            
            print(f"\n{name}:")
            print(f"  Free Only: {'✅ YES' if provider_free_only else '⚠️ NO'}")
            print(f"  Max Cost: ${provider_max_cost}")
            print(f"  Model Filter: {model_filter.get('mode', 'Not set')}")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        show_free_models_status()
    else:
        success = enable_free_models_only()
        sys.exit(0 if success else 1)
