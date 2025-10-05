#!/usr/bin/env python3
"""
Cloud Provider Health Monitoring

Enhanced health checking specifically for cloud AI providers
(OpenRouter, Hugging Face, Together AI, etc.)
"""

import logging
import time
import requests
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class CloudProviderHealth:
    """Health status for a cloud provider"""
    name: str
    healthy: bool
    last_check: datetime
    latency_ms: float
    available_models: List[str] = field(default_factory=list)
    error: Optional[str] = None
    consecutive_failures: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "healthy": self.healthy,
            "last_check": self.last_check.isoformat(),
            "latency_ms": self.latency_ms,
            "available_models": self.available_models[:5],  # First 5 models
            "model_count": len(self.available_models),
            "error": self.error,
            "consecutive_failures": self.consecutive_failures,
            "success_rate": self.successful_requests / max(self.total_requests, 1) * 100
        }


class CloudProviderHealthMonitor:
    """
    Monitors health of all cloud providers and provides detailed diagnostics
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize cloud provider health monitor
        
        Args:
            config_path: Path to token manager config
        """
        self.config_path = config_path or str(Path.home() / ".token_manager_config.json")
        self.provider_health: Dict[str, CloudProviderHealth] = {}
        self.last_full_check = None
        
    def load_providers(self) -> List[Dict]:
        """Load provider configurations from config file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Get active cloud providers (not Exo)
            providers = [
                p for p in config.get('providers', [])
                if p.get('status') == 'active' and p.get('type') != 'local'
            ]
            
            return providers
        except Exception as e:
            logger.error(f"Failed to load providers: {e}")
            return []
    
    def check_provider_health(self, provider: Dict) -> CloudProviderHealth:
        """
        Check health of a single cloud provider
        
        Args:
            provider: Provider configuration dict
            
        Returns:
            CloudProviderHealth object
        """
        name = provider.get('name', 'Unknown')
        start_time = time.time()
        
        # Get previous health if exists
        prev_health = self.provider_health.get(name)
        consecutive_failures = prev_health.consecutive_failures if prev_health else 0
        total_requests = prev_health.total_requests if prev_health else 0
        successful_requests = prev_health.successful_requests if prev_health else 0
        
        try:
            # Get API key
            api_key = provider.get('api_key') or provider.get('api_key_encrypted')
            if not api_key:
                return CloudProviderHealth(
                    name=name,
                    healthy=False,
                    last_check=datetime.now(),
                    latency_ms=0,
                    error="No API key configured",
                    consecutive_failures=consecutive_failures + 1,
                    total_requests=total_requests + 1,
                    successful_requests=successful_requests
                )
            
            # Build headers
            headers = provider.get('headers', {}).copy()
            headers['Authorization'] = f"Bearer {api_key}"
            
            # Try to fetch models list
            base_url = provider.get('base_url')
            models_endpoint = provider.get('models_endpoint', 'v1/models')
            
            # Handle different URL formats
            if models_endpoint.startswith('http'):
                url = models_endpoint
            else:
                url = f"{base_url}/{models_endpoint}"
            
            logger.info(f"Checking {name} health at {url}")
            
            response = requests.get(
                url,
                headers=headers,
                timeout=10
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # Parse models
                data = response.json()
                models = data.get('data', data.get('models', []))
                
                # Extract model IDs
                model_ids = []
                if isinstance(models, list):
                    for model in models:
                        if isinstance(model, dict):
                            model_id = model.get('id', model.get('name'))
                            if model_id:
                                model_ids.append(model_id)
                        elif isinstance(model, str):
                            model_ids.append(model)
                
                logger.info(f"{name} healthy: {len(model_ids)} models available")
                
                return CloudProviderHealth(
                    name=name,
                    healthy=True,
                    last_check=datetime.now(),
                    latency_ms=latency_ms,
                    available_models=model_ids,
                    consecutive_failures=0,
                    total_requests=total_requests + 1,
                    successful_requests=successful_requests + 1
                )
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.warning(f"{name} health check failed: {error_msg}")
                
                return CloudProviderHealth(
                    name=name,
                    healthy=False,
                    last_check=datetime.now(),
                    latency_ms=latency_ms,
                    error=error_msg,
                    consecutive_failures=consecutive_failures + 1,
                    total_requests=total_requests + 1,
                    successful_requests=successful_requests
                )
                
        except requests.exceptions.Timeout:
            error_msg = "Request timeout (>10s)"
            logger.error(f"{name} health check timeout")
            return CloudProviderHealth(
                name=name,
                healthy=False,
                last_check=datetime.now(),
                latency_ms=10000,
                error=error_msg,
                consecutive_failures=consecutive_failures + 1,
                total_requests=total_requests + 1,
                successful_requests=successful_requests
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"{name} health check failed: {e}")
            return CloudProviderHealth(
                name=name,
                healthy=False,
                last_check=datetime.now(),
                latency_ms=(time.time() - start_time) * 1000,
                error=error_msg,
                consecutive_failures=consecutive_failures + 1,
                total_requests=total_requests + 1,
                successful_requests=successful_requests
            )
    
    def check_all_providers(self) -> Dict[str, CloudProviderHealth]:
        """
        Check health of all configured cloud providers
        
        Returns:
            Dictionary of provider name to CloudProviderHealth
        """
        logger.info("Running full cloud provider health check")
        
        providers = self.load_providers()
        
        if not providers:
            logger.warning("No active cloud providers found")
            return {}
        
        for provider in providers:
            health = self.check_provider_health(provider)
            self.provider_health[health.name] = health
        
        self.last_full_check = datetime.now()
        
        # Log summary
        healthy_count = sum(1 for h in self.provider_health.values() if h.healthy)
        total_count = len(self.provider_health)
        logger.info(f"Cloud provider health check complete: {healthy_count}/{total_count} healthy")
        
        return self.provider_health
    
    def get_healthy_providers(self) -> List[str]:
        """Get list of healthy provider names"""
        return [
            name for name, health in self.provider_health.items()
            if health.healthy
        ]
    
    def get_provider_for_model(self, model: str) -> Optional[str]:
        """
        Find a healthy provider that supports the given model
        
        Args:
            model: Model ID/name
            
        Returns:
            Provider name or None
        """
        for name, health in self.provider_health.items():
            if health.healthy and model in health.available_models:
                return name
        return None
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get summary of all provider health statuses"""
        return {
            "providers": {
                name: health.to_dict()
                for name, health in self.provider_health.items()
            },
            "summary": {
                "total": len(self.provider_health),
                "healthy": len(self.get_healthy_providers()),
                "last_check": self.last_full_check.isoformat() if self.last_full_check else None
            }
        }
    
    def test_chat_request(self, provider_name: str, model: str = None) -> Tuple[bool, str]:
        """
        Test a chat request to a specific provider
        
        Args:
            provider_name: Name of provider to test
            model: Optional model to test (uses first available if not specified)
            
        Returns:
            Tuple of (success, message)
        """
        providers = self.load_providers()
        provider = next((p for p in providers if p.get('name') == provider_name), None)
        
        if not provider:
            return False, f"Provider {provider_name} not found"
        
        health = self.provider_health.get(provider_name)
        if not health or not health.healthy:
            return False, f"Provider {provider_name} is not healthy"
        
        # Use first available model if not specified
        if not model and health.available_models:
            model = health.available_models[0]
        
        if not model:
            return False, "No model specified or available"
        
        try:
            # Build request
            api_key = provider.get('api_key') or provider.get('api_key_encrypted')
            headers = provider.get('headers', {}).copy()
            headers['Authorization'] = f"Bearer {api_key}"
            
            base_url = provider.get('base_url')
            chat_endpoint = provider.get('chat_endpoint', 'v1/chat/completions')
            
            if chat_endpoint.startswith('http'):
                url = chat_endpoint
            else:
                url = f"{base_url}/{chat_endpoint}"
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return True, f"Success! Model {model} responded correctly"
            else:
                return False, f"HTTP {response.status_code}: {response.text[:200]}"
                
        except Exception as e:
            return False, f"Request failed: {e}"


# Singleton instance
_monitor = None

def get_cloud_health_monitor() -> CloudProviderHealthMonitor:
    """Get or create the global cloud health monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = CloudProviderHealthMonitor()
    return _monitor
