#!/usr/bin/env python3
"""
Setup script for AI Token Manager + Exo Bridge

Handles installation, configuration, and linking to parent repos.
"""

import os
import sys
import json
import shutil
from pathlib import Path

def setup():
    """Main setup function"""
    print("🌉 AI Token Manager + Exo Bridge Setup")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 12):
        print("❌ Python 3.12+ required")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Get paths
    home = Path.home()
    bridge_dir = Path(__file__).parent
    token_manager_dir = home / "ai-token-manager"
    exo_dir = home / "exo"
    
    # Check parent repos exist
    print("\nChecking parent repositories...")
    
    if not token_manager_dir.exists():
        print(f"⚠️  ai-token-manager not found at {token_manager_dir}")
        print("   Clone it: git clone https://github.com/zebadiee/ai-token-manager.git ~/ai-token-manager")
    else:
        print(f"✓ ai-token-manager found")
    
    if not exo_dir.exists():
        print(f"⚠️  Exo not found at {exo_dir}")
        print("   Clone it: git clone https://github.com/exo-explore/exo.git ~/exo")
    else:
        print(f"✓ Exo found")
    
    # Create config directory
    print("\nSetting up configuration...")
    config_dir = bridge_dir / "config"
    config_dir.mkdir(exist_ok=True)
    
    # Create .env from example if not exists
    env_file = bridge_dir / ".env"
    env_example = bridge_dir / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✓ Created .env from template")
    
    # Create logs directory
    logs_dir = bridge_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    print("✓ Created logs directory")
    
    # Create default bridge config if not exists
    bridge_config = config_dir / "bridge_config.yaml"
    if not bridge_config.exists():
        default_config = """# AI Token Manager + Exo Bridge Configuration

exo:
  primary_host: localhost
  primary_port: 8000
  auto_discover: true
  health_check_interval: 10
  node_timeout: 30

failover:
  enabled: true
  prefer_local: true
  cloud_providers:
    - openrouter
    - huggingface

monitoring:
  enable_hud: false
  hud_port: 8501
  metrics_retention: 100

integration:
  token_manager_config: ~/.token_manager_config.json
  auto_add_exo_provider: true
  exo_provider_priority: 0

logging:
  level: INFO
  file: logs/bridge.log
  max_size_mb: 10
  backup_count: 3
"""
        bridge_config.write_text(default_config)
        print("✓ Created default bridge_config.yaml")
    
    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Start Exo: cd ~/exo && python3 main.py")
    print("3. Run bridge: python src/bridge_manager.py --with-hud")
    print("4. Check examples: python examples/basic_usage.py")
    print("\nDocumentation: docs/")
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "install":
        setup()
    else:
        print("Usage: python setup.py install")
        sys.exit(1)
