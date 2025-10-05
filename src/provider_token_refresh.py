#!/usr/bin/env python3
"""
Provider Token Refresh Manager

Handles token updates with:
- Full system reload on token change
- Config file updates
- Cache invalidation
- Model catalog resync
- Health check reset
"""

import logging
import json
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class ProviderTokenRefreshManager:
    """
    Manages provider token updates and ensures clean system state
    
    On token change:
    1. Updates config file
    2. Invalidates all caches
    3. Resyncs model catalogs
    4. Resets health checks
    5. Triggers preflight validation
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize refresh manager
        
        Args:
            config_path: Path to token manager config
        """
        self.config_path = config_path or str(Path.home() / ".token_manager_config.json")
        self.token_hashes: Dict[str, str] = {}  # provider -> token hash
        
        # Load current hashes
        self._load_token_hashes()
    
    def _load_token_hashes(self):
        """Load current token hashes from config"""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                for provider in config.get('providers', []):
                    name = provider.get('name')
                    token = provider.get('api_key', '')
                    if name and token:
                        self.token_hashes[name] = self._hash_token(token)
        except Exception as e:
            logger.error(f"Failed to load token hashes: {e}")
    
    def update_provider_token(
        self,
        provider_name: str,
        new_token: str,
        auto_activate: bool = True
    ) -> bool:
        """
        Update provider token with full refresh protocol
        
        Args:
            provider_name: Name of provider
            new_token: New API token/key
            auto_activate: Automatically activate provider
            
        Returns:
            True if update successful
        """
        logger.info(f"Updating token for {provider_name}...")
        
        # Check if token actually changed
        new_hash = self._hash_token(new_token)
        old_hash = self.token_hashes.get(provider_name)
        
        if old_hash == new_hash:
            logger.info(f"Token for {provider_name} unchanged, skipping refresh")
            return True
        
        try:
            # Step 1: Update config file
            if not self._update_config_file(provider_name, new_token, auto_activate):
                return False
            
            # Step 2: Clear all caches
            self._clear_caches(provider_name)
            
            # Step 3: Reset health checks
            self._reset_health_checks(provider_name)
            
            # Step 4: Trigger preflight validation
            validation_ok = self._run_preflight(provider_name, new_token)
            
            # Step 5: Resync model catalog
            if validation_ok:
                self._resync_models(provider_name, new_token)
            
            # Update hash
            self.token_hashes[provider_name] = new_hash
            
            logger.info(f"✅ Token update complete for {provider_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update token for {provider_name}: {e}")
            return False
    
    def _update_config_file(
        self,
        provider_name: str,
        new_token: str,
        auto_activate: bool
    ) -> bool:
        """Update config file with new token"""
        try:
            config_path = Path(self.config_path)
            
            if not config_path.exists():
                logger.error(f"Config file not found: {config_path}")
                return False
            
            # Load config
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Find and update provider
            provider_found = False
            for provider in config.get('providers', []):
                if provider.get('name') == provider_name:
                    provider['api_key'] = new_token
                    if auto_activate:
                        provider['status'] = 'active'
                    provider['last_updated'] = datetime.now().isoformat()
                    provider_found = True
                    break
            
            if not provider_found:
                logger.warning(f"Provider {provider_name} not in config, adding...")
                # Add new provider
                if 'providers' not in config:
                    config['providers'] = []
                
                config['providers'].append({
                    'name': provider_name,
                    'api_key': new_token,
                    'status': 'active' if auto_activate else 'inactive',
                    'type': 'cloud',
                    'last_updated': datetime.now().isoformat()
                })
            
            # Save config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Updated config file for {provider_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update config file: {e}")
            return False
    
    def _clear_caches(self, provider_name: str):
        """Clear all caches for provider"""
        try:
            # Clear preflight cache
            from provider_preflight import get_preflight_validator
            validator = get_preflight_validator()
            validator.validation_cache.clear()
            logger.info(f"Cleared preflight cache for {provider_name}")
            
            # Clear model sync cache
            from model_ui_sync import get_sync_enforcer
            enforcer = get_sync_enforcer()
            enforcer.clear_cache(provider_name)
            logger.info(f"Cleared model sync cache for {provider_name}")
            
        except Exception as e:
            logger.warning(f"Failed to clear some caches: {e}")
    
    def _reset_health_checks(self, provider_name: str):
        """Reset health check state for provider"""
        try:
            from cloud_provider_health import CloudProviderHealthMonitor
            
            # This will force fresh health check
            monitor = CloudProviderHealthMonitor(self.config_path)
            if hasattr(monitor, 'provider_health'):
                monitor.provider_health.pop(provider_name, None)
            
            logger.info(f"Reset health checks for {provider_name}")
            
        except Exception as e:
            logger.warning(f"Failed to reset health checks: {e}")
    
    def _run_preflight(self, provider_name: str, api_token: str) -> bool:
        """Run preflight validation with new token"""
        try:
            from provider_preflight import get_preflight_validator
            
            validator = get_preflight_validator()
            
            # Build minimal config for validation
            provider_config = {
                'name': provider_name,
                'api_key': api_token,
                'status': 'active'
            }
            
            # Add provider-specific endpoints
            if provider_name == "OpenRouter":
                provider_config.update({
                    'base_url': 'https://openrouter.ai/api',
                    'list_models_endpoint': 'v1/models',
                    'chat_endpoint': 'v1/chat/completions',
                    'headers': {'HTTP-Referer': 'spiral-codex-hud'}
                })
            elif provider_name == "Hugging Face":
                provider_config.update({
                    'base_url': 'https://api-inference.huggingface.co',
                    'list_models_endpoint': 'https://huggingface.co/api/models'
                })
            elif provider_name == "Together AI":
                provider_config.update({
                    'base_url': 'https://api.together.xyz',
                    'list_models_endpoint': 'v1/models',
                    'chat_endpoint': 'v1/chat/completions'
                })
            
            # Run validation
            result = validator.validate_provider(
                provider_name,
                provider_config,
                force_refresh=True
            )
            
            if result.success:
                logger.info(f"✅ Preflight passed for {provider_name}: {len(result.available_models)} models")
                return True
            else:
                logger.error(f"❌ Preflight failed for {provider_name}: {result.error_message}")
                return False
                
        except Exception as e:
            logger.error(f"Preflight validation failed: {e}")
            return False
    
    def _resync_models(self, provider_name: str, api_token: str):
        """Resync model catalog with new token"""
        try:
            from model_ui_sync import get_sync_enforcer
            
            enforcer = get_sync_enforcer()
            catalog = enforcer.sync_provider_models(
                provider_name,
                api_token,
                force_refresh=True
            )
            
            logger.info(
                f"Resynced models for {provider_name}: "
                f"{len(catalog.models)} models, "
                f"validation={'passed' if catalog.validation_passed else 'failed'}"
            )
            
        except Exception as e:
            logger.warning(f"Failed to resync models: {e}")
    
    def _hash_token(self, token: str) -> str:
        """Hash token for comparison"""
        return hashlib.sha256(token.encode()).hexdigest()[:16]
    
    def detect_token_change(self, provider_name: str, current_token: str) -> bool:
        """
        Detect if token has changed
        
        Args:
            provider_name: Provider name
            current_token: Current token value
            
        Returns:
            True if token changed
        """
        current_hash = self._hash_token(current_token)
        old_hash = self.token_hashes.get(provider_name)
        
        return old_hash != current_hash
    
    def get_refresh_status(self) -> Dict[str, Dict]:
        """Get refresh status for all providers"""
        status = {}
        
        try:
            config_path = Path(self.config_path)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                for provider in config.get('providers', []):
                    name = provider.get('name')
                    if name:
                        status[name] = {
                            'has_token': bool(provider.get('api_key')),
                            'is_active': provider.get('status') == 'active',
                            'last_updated': provider.get('last_updated', 'unknown'),
                            'token_hash': self.token_hashes.get(name, 'none')
                        }
        except Exception as e:
            logger.error(f"Failed to get refresh status: {e}")
        
        return status


# Singleton instance
_refresh_manager = None


def get_refresh_manager(config_path: Optional[str] = None) -> ProviderTokenRefreshManager:
    """Get or create global refresh manager"""
    global _refresh_manager
    if _refresh_manager is None:
        _refresh_manager = ProviderTokenRefreshManager(config_path)
    return _refresh_manager


# Streamlit integration
def streamlit_token_updater(provider_name: str, widget_key: str = "token_input"):
    """
    Streamlit widget for token updates with auto-refresh
    
    Args:
        provider_name: Provider name
        widget_key: Streamlit widget key
    """
    import streamlit as st
    
    refresh_manager = get_refresh_manager()
    
    # Token input
    new_token = st.text_input(
        f"{provider_name} API Key",
        type="password",
        key=widget_key,
        help=f"Enter {provider_name} API key. Changes trigger full refresh."
    )
    
    # Update button
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button(f"Update {provider_name} Token", width="stretch"):
            if not new_token:
                st.error("Please enter a token")
            else:
                with st.spinner(f"Updating {provider_name} token..."):
                    success = refresh_manager.update_provider_token(
                        provider_name,
                        new_token,
                        auto_activate=True
                    )
                    
                    if success:
                        st.success(f"✅ {provider_name} token updated and validated!")
                        st.info("🔄 Full system refresh complete. Ready to use.")
                        st.balloons()
                    else:
                        st.error(f"❌ Failed to update {provider_name} token")
                        st.info("Check logs for details")
    
    with col2:
        # Auto-detect change
        if new_token and refresh_manager.detect_token_change(provider_name, new_token):
            st.warning("Token changed")
