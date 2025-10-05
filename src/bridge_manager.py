#!/usr/bin/env python3
"""
Bridge Manager - Main Orchestrator

Ties together all bridge components:
- Exo provider adapter
- Health monitoring
- Failover management
- HUD dashboard (optional)
"""

import sys
import os
import argparse
import logging
import signal
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Add parent repos to path
sys.path.insert(0, str(Path.home() / "ai-token-manager"))
sys.path.insert(0, str(Path.home() / "exo"))

from exo_provider import ExoClusterProvider
from exo_integration import ExoTokenManagerIntegration

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExoBridgeManager:
    """
    Main bridge manager orchestrating all components
    
    Features:
    - Connects token manager with Exo
    - Manages health monitoring
    - Handles failover logic
    - Optional HUD dashboard
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        token_manager_config: Optional[str] = None,
        exo_host: str = "localhost",
        exo_port: int = 8000,
        enable_hud: bool = False,
        hud_port: int = 8501
    ):
        """
        Initialize bridge manager
        
        Args:
            config_path: Path to bridge config YAML
            token_manager_config: Path to token manager config
            exo_host: Exo cluster host
            exo_port: Exo cluster port
            enable_hud: Start HUD dashboard
            hud_port: HUD port
        """
        # Load environment
        load_dotenv()
        
        # Load config
        self.config = self._load_config(config_path)
        
        # Override with params
        if token_manager_config:
            self.config['integration']['token_manager_config'] = token_manager_config
        
        exo_host = exo_host or self.config.get('exo', {}).get('primary_host', 'localhost')
        exo_port = exo_port or self.config.get('exo', {}).get('primary_port', 8000)
        
        # Initialize integration
        logger.info(f"Initializing bridge with Exo at {exo_host}:{exo_port}")
        
        self.integration = ExoTokenManagerIntegration(
            config_path=self.config['integration']['token_manager_config'],
            exo_host=exo_host,
            exo_port=exo_port,
            enable_auto_failover=self.config['failover']['enabled'],
            exo_priority=self.config['integration']['exo_provider_priority']
        )
        
        self.enable_hud = enable_hud or self.config['monitoring']['enable_hud']
        self.hud_port = hud_port or self.config['monitoring']['hud_port']
        self.running = False
        
        # Setup signal handlers (only in main thread)
        import threading
        if threading.current_thread() == threading.main_thread():
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not config_path:
            config_path = Path(__file__).parent.parent / "config" / "bridge_config.yaml"
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded config from {config_path}")
            return config
        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using defaults")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'exo': {
                'primary_host': 'localhost',
                'primary_port': 8000,
                'auto_discover': True,
                'health_check_interval': 10,
                'node_timeout': 30
            },
            'failover': {
                'enabled': True,
                'prefer_local': True,
                'cloud_providers': ['openrouter', 'huggingface']
            },
            'monitoring': {
                'enable_hud': False,
                'hud_port': 8501,
                'metrics_retention': 100
            },
            'integration': {
                'token_manager_config': '~/.token_manager_config.json',
                'auto_add_exo_provider': True,
                'exo_provider_priority': 0
            }
        }
    
    def start(self):
        """Start bridge services"""
        logger.info("Starting AI Token Manager + Exo Bridge...")
        
        # Start integration
        self.integration.start()
        self.running = True
        
        logger.info("✓ Bridge started successfully")
        
        # Show status
        status = self.get_status()
        logger.info(f"Exo cluster: {status['exo']['available']}")
        logger.info(f"Healthy nodes: {status['exo']['health']['healthy_nodes']}")
        logger.info(f"Auto-failover: {self.config['failover']['enabled']}")
        
        # Start HUD if enabled
        if self.enable_hud:
            self._start_hud()
    
    def stop(self):
        """Stop bridge services"""
        logger.info("Stopping bridge...")
        
        if self.integration:
            self.integration.stop()
        
        self.running = False
        logger.info("✓ Bridge stopped")
    
    def _start_hud(self):
        """Start HUD dashboard"""
        import subprocess
        
        logger.info(f"Starting Spiral Codex HUD on port {self.hud_port}...")
        
        hud_script = Path(__file__).parent / "spiral_codex_hud.py"
        
        try:
            subprocess.Popen([
                "streamlit", "run",
                str(hud_script),
                f"--server.port={self.hud_port}",
                "--server.headless=true"
            ])
            logger.info(f"✓ HUD started at http://localhost:{self.hud_port}")
        except Exception as e:
            logger.error(f"Failed to start HUD: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def chat_completion(
        self,
        messages: List[Dict],
        model: str = "llama-3.2-3b",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request through bridge
        
        Args:
            messages: List of message dicts
            model: Model name
            **kwargs: Additional parameters
        
        Returns:
            Dict with response, provider_used, cost
        """
        # Create cloud provider callback using direct API calls
        def cloud_provider_callback(model, messages, **kwargs):
            """Callback to use cloud providers directly"""
            try:
                import json
                import requests
                
                # Load provider config
                config_path = Path.home() / ".token_manager_config.json"
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Find active cloud providers (skip Exo)
                providers = [p for p in config.get('providers', []) 
                           if p.get('status') == 'active' and p.get('type') != 'local']
                
                if not providers:
                    return {}, "No cloud providers configured"
                
                # Try each provider in priority order
                providers.sort(key=lambda x: x.get('priority', 999))
                
                for provider in providers:
                    try:
                        provider_name = provider.get('name')
                        base_url = provider.get('base_url')
                        chat_endpoint = provider.get('chat_endpoint')
                        headers = provider.get('headers', {})
                        
                        # Get API key
                        api_key = provider.get('api_key')
                        if not api_key and provider.get('api_key_encrypted'):
                            # Decrypt if needed (simplified - just use as-is for now)
                            api_key = provider.get('api_key_encrypted')
                        
                        if not api_key:
                            continue
                        
                        # Add authorization header
                        headers['Authorization'] = f"Bearer {api_key}"
                        
                        # Build request
                        url = f"{base_url}/{chat_endpoint}" if not chat_endpoint.startswith('http') else chat_endpoint
                        payload = {
                            "model": model,
                            "messages": messages,
                            **kwargs
                        }
                        
                        logger.info(f"Trying cloud provider: {provider_name}")
                        
                        # Make request
                        response = requests.post(url, json=payload, headers=headers, timeout=30)
                        
                        if response.status_code == 200:
                            logger.info(f"Success with {provider_name}")
                            return response.json(), None
                        else:
                            logger.warning(f"{provider_name} returned {response.status_code}")
                            continue
                            
                    except Exception as e:
                        logger.error(f"Provider {provider.get('name')} failed: {e}")
                        continue
                
                return {}, "All cloud providers failed"
                
            except Exception as e:
                logger.error(f"Cloud provider callback failed: {e}")
                return {}, str(e)
        
        # Route request with cloud failover
        response, error, provider = self.integration.route_request(
            model=model,
            messages=messages,
            cloud_provider_callback=cloud_provider_callback,
            **kwargs
        )
        
        return {
            "response": response,
            "error": error,
            "provider_used": provider,
            "cost": 0.0 if "Exo" in provider else None
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive bridge status"""
        return self.integration.get_unified_status()


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="AI Token Manager + Exo Bridge Manager"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to bridge config YAML"
    )
    parser.add_argument(
        "--exo-host",
        type=str,
        default="localhost",
        help="Exo cluster host"
    )
    parser.add_argument(
        "--exo-port",
        type=int,
        default=8000,
        help="Exo cluster port"
    )
    parser.add_argument(
        "--with-hud",
        action="store_true",
        help="Start HUD dashboard"
    )
    parser.add_argument(
        "--hud-port",
        type=int,
        default=8501,
        help="HUD port"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test request and exit"
    )
    parser.add_argument(
        "--auto-port",
        action="store_true",
        default=True,
        help="Automatically find available port if default is in use"
    )
    
    args = parser.parse_args()
    
    # Check if requested ports are available
    exo_host = args.exo_host
    exo_port = args.exo_port
    
    if args.auto_port:
        # Try to import port utilities
        try:
            from port_utils import is_port_available, find_available_port
            
            # Check Exo port
            if not is_port_available(exo_port, exo_host):
                logger.warning(f"Exo port {exo_port} is in use")
                try:
                    new_port = find_available_port(exo_port, exo_host, port_range=50)
                    logger.info(f"Using alternative Exo port: {new_port}")
                    exo_port = new_port
                except RuntimeError as e:
                    logger.error(f"Could not find available port: {e}")
            
            # Check HUD port if starting HUD
            if args.with_hud:
                hud_port = args.hud_port
                if not is_port_available(hud_port):
                    logger.warning(f"HUD port {hud_port} is in use")
                    try:
                        new_port = find_available_port(hud_port, port_range=50)
                        logger.info(f"Using alternative HUD port: {new_port}")
                        args.hud_port = new_port
                    except RuntimeError as e:
                        logger.error(f"Could not find available HUD port: {e}")
        
        except ImportError:
            logger.debug("Port utilities not available, using specified ports")
    
    # Initialize bridge
    bridge = ExoBridgeManager(
        config_path=args.config,
        exo_host=exo_host,
        exo_port=exo_port,
        enable_hud=args.with_hud,
        hud_port=args.hud_port
    )
    
    # Start services
    bridge.start()
    
    # Test mode
    if args.test:
        logger.info("Running test request...")
        result = bridge.chat_completion(
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=50
        )
        
        logger.info(f"Provider: {result['provider_used']}")
        logger.info(f"Error: {result['error']}")
        
        if not result['error']:
            content = result['response'].get('choices', [{}])[0].get('message', {}).get('content', '')
            logger.info(f"Response: {content}")
        
        bridge.stop()
        return
    
    # Keep running
    logger.info("\n" + "=" * 60)
    logger.info("Bridge is running. Press Ctrl+C to stop.")
    logger.info(f"Exo cluster: http://{exo_host}:{exo_port}")
    if args.with_hud:
        logger.info(f"HUD dashboard: http://localhost:{args.hud_port}")
    logger.info("=" * 60)
    
    try:
        while bridge.running:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        bridge.stop()


if __name__ == "__main__":
    main()
