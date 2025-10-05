#!/usr/bin/env python3
"""
API Key Secure Storage and Lock-In System

Provides secure API key management with:
- Encrypted storage
- Lock/unlock functionality
- Persistent across restarts
- UI integration helpers
"""

import json
import base64
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime
from cryptography.fernet import Fernet
import hashlib
import logging

logger = logging.getLogger(__name__)


class SecureKeyManager:
    """
    Manages API keys with encryption and lock/unlock functionality
    
    Features:
    - Encrypted storage on disk
    - Lock state management
    - Auto-load on startup
    - Streamlit UI integration
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize secure key manager
        
        Args:
            config_path: Path to config file (default: ~/.spiral_codex_keys.json)
        """
        self.config_path = config_path or str(Path.home() / ".spiral_codex_keys.json")
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        self.keys: Dict[str, Dict] = {}
        
        # Load existing keys
        self.load_keys()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for this machine"""
        key_file = Path.home() / ".spiral_codex_encryption_key"
        
        if key_file.exists():
            return key_file.read_bytes()
        else:
            # Generate new key
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            key_file.chmod(0o600)  # Read/write for owner only
            return key
    
    def save_key(
        self,
        provider_name: str,
        api_key: str,
        locked: bool = True,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Save API key with encryption
        
        Args:
            provider_name: Name of provider (e.g., "OpenRouter")
            api_key: The API key to save
            locked: Whether key should be locked by default
            metadata: Optional metadata (permissions, scopes, etc.)
            
        Returns:
            True if successful
        """
        try:
            # Encrypt the key
            encrypted_key = self.cipher.encrypt(api_key.encode()).decode()
            
            # Store with metadata
            self.keys[provider_name] = {
                'encrypted_key': encrypted_key,
                'locked': locked,
                'saved_at': datetime.now().isoformat(),
                'key_hash': hashlib.sha256(api_key.encode()).hexdigest()[:16],
                'metadata': metadata or {}
            }
            
            # Save to disk
            self._save_to_disk()
            
            logger.info(f"Saved and {'locked' if locked else 'unlocked'} key for {provider_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save key for {provider_name}: {e}")
            return False
    
    def get_key(self, provider_name: str) -> Optional[str]:
        """
        Get decrypted API key
        
        Args:
            provider_name: Name of provider
            
        Returns:
            Decrypted API key or None if not found
        """
        if provider_name not in self.keys:
            return None
        
        try:
            encrypted_key = self.keys[provider_name]['encrypted_key']
            decrypted = self.cipher.decrypt(encrypted_key.encode()).decode()
            return decrypted
        except Exception as e:
            logger.error(f"Failed to decrypt key for {provider_name}: {e}")
            return None
    
    def is_locked(self, provider_name: str) -> bool:
        """Check if a key is locked"""
        if provider_name not in self.keys:
            return False
        return self.keys[provider_name].get('locked', False)
    
    def lock_key(self, provider_name: str) -> bool:
        """Lock a key (prevent editing)"""
        if provider_name not in self.keys:
            return False
        
        self.keys[provider_name]['locked'] = True
        self.keys[provider_name]['locked_at'] = datetime.now().isoformat()
        self._save_to_disk()
        
        logger.info(f"Locked key for {provider_name}")
        return True
    
    def unlock_key(self, provider_name: str) -> bool:
        """Unlock a key (allow editing)"""
        if provider_name not in self.keys:
            return False
        
        self.keys[provider_name]['locked'] = False
        self.keys[provider_name]['unlocked_at'] = datetime.now().isoformat()
        self._save_to_disk()
        
        logger.info(f"Unlocked key for {provider_name}")
        return True
    
    def delete_key(self, provider_name: str) -> bool:
        """Delete a stored key"""
        if provider_name in self.keys:
            del self.keys[provider_name]
            self._save_to_disk()
            logger.info(f"Deleted key for {provider_name}")
            return True
        return False
    
    def has_key(self, provider_name: str) -> bool:
        """Check if provider has a saved key"""
        return provider_name in self.keys
    
    def get_key_info(self, provider_name: str) -> Optional[Dict]:
        """Get key metadata without decrypting the key"""
        if provider_name not in self.keys:
            return None
        
        info = self.keys[provider_name].copy()
        # Don't return the encrypted key
        info.pop('encrypted_key', None)
        return info
    
    def list_providers(self) -> list:
        """List all providers with saved keys"""
        return list(self.keys.keys())
    
    def load_keys(self) -> bool:
        """Load keys from disk"""
        try:
            if not Path(self.config_path).exists():
                self.keys = {}
                return True
            
            with open(self.config_path, 'r') as f:
                self.keys = json.load(f)
            
            logger.info(f"Loaded {len(self.keys)} saved keys")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load keys: {e}")
            self.keys = {}
            return False
    
    def _save_to_disk(self) -> bool:
        """Save keys to disk"""
        try:
            # Ensure parent directory exists
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write to temp file first
            temp_path = f"{self.config_path}.tmp"
            with open(temp_path, 'w') as f:
                json.dump(self.keys, f, indent=2)
            
            # Atomic rename
            Path(temp_path).replace(self.config_path)
            
            # Set secure permissions
            Path(self.config_path).chmod(0o600)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save keys: {e}")
            return False


# Streamlit UI Integration
def streamlit_secure_key_input(
    provider_name: str,
    key_manager: SecureKeyManager,
    label: Optional[str] = None,
    help_text: Optional[str] = None
) -> Tuple[str, bool]:
    """
    Streamlit widget for secure key input with lock/unlock
    
    Args:
        provider_name: Name of provider
        key_manager: SecureKeyManager instance
        label: Optional custom label
        help_text: Optional help text
        
    Returns:
        (api_key, was_changed)
    """
    import streamlit as st
    
    label = label or f"{provider_name} API Key"
    help_text = help_text or f"API key for {provider_name}"
    
    # Check if key exists and is locked
    has_key = key_manager.has_key(provider_name)
    is_locked = key_manager.is_locked(provider_name) if has_key else False
    
    # Get current key (masked if locked)
    current_key = ""
    if has_key:
        if is_locked:
            # Show masked version
            key_info = key_manager.get_key_info(provider_name)
            current_key = f"••••••••{key_info['key_hash']}"
        else:
            # Show actual key for editing
            current_key = key_manager.get_key(provider_name) or ""
    
    # Create columns for input and buttons
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        # Input field (disabled if locked)
        new_key = st.text_input(
            label,
            value=current_key,
            type="password" if not is_locked else "default",
            disabled=is_locked,
            help=help_text,
            key=f"{provider_name}_key_input"
        )
    
    with col2:
        if is_locked:
            # Show unlock button
            if st.button("🔓 Unlock", key=f"{provider_name}_unlock"):
                key_manager.unlock_key(provider_name)
                st.rerun()
        else:
            # Show lock button
            if st.button("🔒 Lock", key=f"{provider_name}_lock"):
                if new_key and not new_key.startswith("••••"):
                    # Save and lock
                    key_manager.save_key(provider_name, new_key, locked=True)
                    st.success(f"✅ {provider_name} key saved and locked!")
                    st.rerun()
                elif has_key:
                    # Just lock existing
                    key_manager.lock_key(provider_name)
                    st.rerun()
    
    with col3:
        if has_key:
            if st.button("🗑️ Delete", key=f"{provider_name}_delete"):
                key_manager.delete_key(provider_name)
                st.warning(f"Deleted {provider_name} key")
                st.rerun()
    
    # Show status
    if has_key:
        key_info = key_manager.get_key_info(provider_name)
        status_emoji = "🔒" if is_locked else "🔓"
        saved_at = key_info.get('saved_at', 'unknown')
        st.caption(f"{status_emoji} Saved: {saved_at[:19]}")
    
    # Return the actual key (decrypted) for use
    actual_key = key_manager.get_key(provider_name) if has_key else new_key
    was_changed = (new_key != current_key) and not new_key.startswith("••••")
    
    return actual_key or "", was_changed


# Singleton instance
_key_manager: Optional[SecureKeyManager] = None


def get_key_manager() -> SecureKeyManager:
    """Get or create global key manager instance"""
    global _key_manager
    if _key_manager is None:
        _key_manager = SecureKeyManager()
    return _key_manager


if __name__ == "__main__":
    # Test the key manager
    manager = SecureKeyManager()
    
    # Save a test key
    manager.save_key("TestProvider", "sk-test-123456789", locked=True)
    
    # Retrieve it
    key = manager.get_key("TestProvider")
    print(f"Retrieved key: {key}")
    
    # Check lock status
    print(f"Is locked: {manager.is_locked('TestProvider')}")
    
    # Get info
    info = manager.get_key_info("TestProvider")
    print(f"Key info: {info}")
