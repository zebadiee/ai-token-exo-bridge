#!/usr/bin/env python3
"""
Model-UI Synchronization Enforcer

Ensures UI dropdowns only show models that are:
1. Actually accessible by the current token
2. Validated through preflight checks
3. Confirmed working via inference test

Zero ghost models. Zero doomed requests.
"""

import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ModelCatalog:
    """Catalog of validated models for a provider"""
    provider_name: str
    models: List[str]
    last_sync: datetime
    token_hash: str  # Hash of API token used
    validation_passed: bool
    error_message: Optional[str] = None
    
    def is_stale(self, ttl_seconds: int = 300) -> bool:
        """Check if catalog needs refresh"""
        age = (datetime.now() - self.last_sync).total_seconds()
        return age > ttl_seconds
    
    def to_dict(self) -> Dict:
        return {
            "provider_name": self.provider_name,
            "models": self.models,
            "last_sync": self.last_sync.isoformat(),
            "token_hash": self.token_hash,
            "validation_passed": self.validation_passed,
            "error_message": self.error_message,
            "model_count": len(self.models)
        }


class ModelUISyncEnforcer:
    """
    Enforces strict synchronization between available models and UI
    
    Key Features:
    - Only validated models shown in UI
    - Auto-refresh on token change
    - Cache with TTL
    - Thread-safe operations
    - Prevents ghost model selection
    """
    
    def __init__(self, cache_ttl: int = 300):
        """
        Initialize sync enforcer
        
        Args:
            cache_ttl: Cache time-to-live in seconds (default: 5 min)
        """
        self.cache_ttl = cache_ttl
        self.catalogs: Dict[str, ModelCatalog] = {}
        self.lock = Lock()
        self.blocked_models: Set[str] = set()  # Models that failed validation
        
    def sync_provider_models(
        self,
        provider_name: str,
        api_token: str,
        force_refresh: bool = False
    ) -> ModelCatalog:
        """
        Sync models for a provider
        
        Args:
            provider_name: Name of provider
            api_token: API token/key
            force_refresh: Force new sync even if cached
            
        Returns:
            ModelCatalog with validated models
        """
        from provider_preflight import get_preflight_validator
        
        token_hash = self._hash_token(api_token)
        
        # Check cache
        with self.lock:
            if not force_refresh and provider_name in self.catalogs:
                cached = self.catalogs[provider_name]
                
                # Use cache if:
                # 1. Same token
                # 2. Not stale
                # 3. Validation passed
                if (cached.token_hash == token_hash and 
                    not cached.is_stale(self.cache_ttl) and
                    cached.validation_passed):
                    logger.info(f"Using cached models for {provider_name}: {len(cached.models)} models")
                    return cached
        
        # Need fresh sync
        logger.info(f"Syncing models for {provider_name}...")
        
        validator = get_preflight_validator()
        
        # Build provider config
        provider_config = {
            "name": provider_name,
            "api_key": api_token,
            "status": "active"
        }
        
        # Add provider-specific config
        if provider_name == "OpenRouter":
            provider_config.update({
                "base_url": "https://openrouter.ai/api",
                "list_models_endpoint": "v1/models",
                "chat_endpoint": "v1/chat/completions",
                "headers": {"HTTP-Referer": "spiral-codex-hud"}
            })
        elif provider_name == "Hugging Face":
            provider_config.update({
                "base_url": "https://api-inference.huggingface.co",
                "list_models_endpoint": "https://huggingface.co/api/models",
                "chat_endpoint": "models/{model}"
            })
        elif provider_name == "Together AI":
            provider_config.update({
                "base_url": "https://api.together.xyz",
                "list_models_endpoint": "v1/models",
                "chat_endpoint": "v1/chat/completions"
            })
        
        # Run validation
        result = validator.validate_provider(
            provider_name,
            provider_config,
            force_refresh=True
        )
        
        # Build catalog
        catalog = ModelCatalog(
            provider_name=provider_name,
            models=result.available_models if result.success else [],
            last_sync=datetime.now(),
            token_hash=token_hash,
            validation_passed=result.success,
            error_message=result.error_message if not result.success else None
        )
        
        # Update cache
        with self.lock:
            self.catalogs[provider_name] = catalog
        
        if result.success:
            logger.info(f"✅ Synced {len(catalog.models)} models for {provider_name}")
        else:
            logger.warning(f"❌ Sync failed for {provider_name}: {result.error_message}")
        
        return catalog
    
    def get_ui_models(
        self,
        provider_name: str,
        api_token: str,
        force_refresh: bool = False
    ) -> List[str]:
        """
        Get models safe for UI display
        
        Only returns models that:
        - Passed preflight validation
        - Are not in blocked list
        - Have valid cache
        
        Args:
            provider_name: Provider name
            api_token: API token
            force_refresh: Force refresh
            
        Returns:
            List of validated model IDs
        """
        catalog = self.sync_provider_models(provider_name, api_token, force_refresh)
        
        if not catalog.validation_passed:
            logger.warning(f"Cannot provide UI models for {provider_name}: validation failed")
            return []
        
        # Filter out blocked models
        with self.lock:
            safe_models = [
                m for m in catalog.models
                if f"{provider_name}:{m}" not in self.blocked_models
            ]
        
        return safe_models
    
    def validate_model_selection(
        self,
        provider_name: str,
        model_id: str,
        api_token: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that a selected model is actually available
        
        Args:
            provider_name: Provider name
            model_id: Model ID selected
            api_token: API token
            
        Returns:
            (is_valid, error_message)
        """
        catalog = self.sync_provider_models(provider_name, api_token, force_refresh=False)
        
        if not catalog.validation_passed:
            return False, f"Provider {provider_name} validation failed: {catalog.error_message}"
        
        if model_id not in catalog.models:
            # Model not in validated list
            available = catalog.models[:5]  # Show first 5
            return False, (
                f"Model '{model_id}' not available for {provider_name}. "
                f"Available models: {', '.join(available)}"
                + (f" (and {len(catalog.models) - 5} more)" if len(catalog.models) > 5 else "")
            )
        
        # Check if blocked
        model_key = f"{provider_name}:{model_id}"
        with self.lock:
            if model_key in self.blocked_models:
                return False, f"Model '{model_id}' is blocked due to previous failures"
        
        return True, None
    
    def block_model(self, provider_name: str, model_id: str, reason: str):
        """
        Block a model from UI selection
        
        Args:
            provider_name: Provider name
            model_id: Model to block
            reason: Reason for blocking
        """
        model_key = f"{provider_name}:{model_id}"
        with self.lock:
            self.blocked_models.add(model_key)
        logger.warning(f"Blocked {model_key}: {reason}")
    
    def unblock_model(self, provider_name: str, model_id: str):
        """Unblock a model"""
        model_key = f"{provider_name}:{model_id}"
        with self.lock:
            self.blocked_models.discard(model_key)
        logger.info(f"Unblocked {model_key}")
    
    def clear_cache(self, provider_name: Optional[str] = None):
        """
        Clear cache for a provider or all providers
        
        Args:
            provider_name: Provider to clear, or None for all
        """
        with self.lock:
            if provider_name:
                self.catalogs.pop(provider_name, None)
                logger.info(f"Cleared cache for {provider_name}")
            else:
                self.catalogs.clear()
                logger.info("Cleared all model caches")
    
    def on_token_change(self, provider_name: str, new_token: str):
        """
        Handle token change event
        
        Forces refresh and clears old cache
        
        Args:
            provider_name: Provider name
            new_token: New API token
        """
        logger.info(f"Token changed for {provider_name}, forcing refresh...")
        
        # Clear cache
        self.clear_cache(provider_name)
        
        # Force new sync
        self.sync_provider_models(provider_name, new_token, force_refresh=True)
    
    def get_catalog_status(self, provider_name: str) -> Optional[Dict]:
        """Get status of a provider's catalog"""
        with self.lock:
            catalog = self.catalogs.get(provider_name)
            if catalog:
                return catalog.to_dict()
        return None
    
    def _hash_token(self, token: str) -> str:
        """Hash token for cache key (first 10 chars for quick compare)"""
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()[:16]
    
    def export_diagnostics(self, path: str):
        """Export diagnostic info to file"""
        with self.lock:
            data = {
                "timestamp": datetime.now().isoformat(),
                "catalogs": {
                    name: catalog.to_dict()
                    for name, catalog in self.catalogs.items()
                },
                "blocked_models": list(self.blocked_models),
                "cache_ttl": self.cache_ttl
            }
        
        Path(path).write_text(json.dumps(data, indent=2))
        logger.info(f"Exported diagnostics to {path}")


# Singleton instance
_sync_enforcer = None


def get_sync_enforcer(cache_ttl: int = 300) -> ModelUISyncEnforcer:
    """Get or create global sync enforcer"""
    global _sync_enforcer
    if _sync_enforcer is None:
        _sync_enforcer = ModelUISyncEnforcer(cache_ttl)
    return _sync_enforcer


# Streamlit integration helper
def streamlit_model_selector(
    provider_name: str,
    api_token: str,
    key: str = "model_selector",
    label: str = "Select Model"
):
    """
    Streamlit widget for validated model selection
    
    Only shows models that passed validation
    
    Args:
        provider_name: Provider name
        api_token: API token
        key: Streamlit widget key
        label: Widget label
        
    Returns:
        Selected model ID or None
    """
    import streamlit as st
    
    enforcer = get_sync_enforcer()
    
    # Get validated models
    models = enforcer.get_ui_models(provider_name, api_token)
    
    if not models:
        catalog_status = enforcer.get_catalog_status(provider_name)
        if catalog_status and not catalog_status['validation_passed']:
            st.error(f"❌ {provider_name}: {catalog_status['error_message']}")
            st.info("👆 Fix the issue above to enable model selection")
        else:
            st.warning(f"No models available for {provider_name}")
        return None
    
    # Show selector
    selected = st.selectbox(
        label,
        options=models,
        key=key,
        help=f"{len(models)} validated models available"
    )
    
    # Validate selection
    if selected:
        valid, error = enforcer.validate_model_selection(provider_name, selected, api_token)
        if not valid:
            st.error(f"❌ {error}")
            return None
    
    return selected
