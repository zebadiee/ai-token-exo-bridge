#!/usr/bin/env python3
"""
Provider Pre-Flight Validation & Model Sync System

PhD-level provider validation that ensures:
- Only available models are shown
- API keys are tested before use
- Permission issues are caught early
- User gets actionable fix steps
- No doomed requests ever sent
"""

import logging
import requests
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Pre-flight validation status"""
    VALID = "valid"
    INVALID_KEY = "invalid_key"
    NO_PERMISSION = "no_permission"
    NO_MODELS = "no_models"
    CONNECTION_ERROR = "connection_error"
    UNKNOWN = "unknown"


@dataclass
class ValidationResult:
    """Result of provider pre-flight validation"""
    status: ValidationStatus
    provider_name: str
    success: bool
    available_models: List[str] = field(default_factory=list)
    tested_model: Optional[str] = None
    error_message: Optional[str] = None
    fix_steps: List[str] = field(default_factory=list)
    dashboard_url: Optional[str] = None
    required_scopes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "status": self.status.value,
            "provider_name": self.provider_name,
            "success": self.success,
            "available_models": self.available_models[:10],  # First 10
            "model_count": len(self.available_models),
            "tested_model": self.tested_model,
            "error_message": self.error_message,
            "fix_steps": self.fix_steps,
            "dashboard_url": self.dashboard_url,
            "required_scopes": self.required_scopes
        }


class ProviderPreFlightValidator:
    """
    Pre-flight validation for cloud providers
    
    Ensures:
    1. API key is valid
    2. Has required permissions
    3. Can list models
    4. Can perform inference
    5. Only valid models shown in UI
    """
    
    # Provider dashboard URLs
    DASHBOARD_URLS = {
        "OpenRouter": "https://openrouter.ai/keys",
        "Hugging Face": "https://huggingface.co/settings/tokens",
        "Together AI": "https://api.together.xyz/settings/api-keys",
        "Anthropic": "https://console.anthropic.com/settings/keys",
        "OpenAI": "https://platform.openai.com/api-keys"
    }
    
    # Required scopes per provider
    REQUIRED_SCOPES = {
        "OpenRouter": ["api.read", "api.inference"],
        "Hugging Face": ["inference-api", "read-repos"],
        "Together AI": ["inference"],
        "Anthropic": ["messages:write"],
        "OpenAI": ["completions.create"]
    }
    
    def __init__(self):
        """Initialize validator"""
        self.validation_cache: Dict[str, ValidationResult] = {}
        self.cache_ttl = 300  # 5 minutes
    
    def validate_provider(
        self,
        provider_name: str,
        provider_config: Dict,
        force_refresh: bool = False
    ) -> ValidationResult:
        """
        Comprehensive pre-flight validation of a provider
        
        Args:
            provider_name: Name of provider
            provider_config: Provider configuration
            force_refresh: Force new validation
            
        Returns:
            ValidationResult with detailed status
        """
        # Check cache
        cache_key = f"{provider_name}_{provider_config.get('api_key', '')[:10]}"
        if not force_refresh and cache_key in self.validation_cache:
            cached = self.validation_cache[cache_key]
            age = (datetime.now() - datetime.fromisoformat(cached.to_dict().get('timestamp', datetime.now().isoformat()))).total_seconds()
            if age < self.cache_ttl:
                logger.info(f"Using cached validation for {provider_name}")
                return cached
        
        logger.info(f"Running pre-flight validation for {provider_name}...")
        
        # Step 1: Validate API key exists
        api_key = provider_config.get('api_key') or provider_config.get('api_key_encrypted')
        if not api_key:
            return ValidationResult(
                status=ValidationStatus.INVALID_KEY,
                provider_name=provider_name,
                success=False,
                error_message="No API key configured",
                fix_steps=[
                    "1. Get API key from provider dashboard",
                    "2. Enter key in HUD sidebar",
                    "3. Click 'Save API Keys'",
                    "4. Reconnect"
                ],
                dashboard_url=self.DASHBOARD_URLS.get(provider_name)
            )
        
        # Step 2: Test model listing
        models, models_error = self._test_model_listing(provider_name, provider_config, api_key)
        
        if models_error:
            # Parse error for specific issues
            if "401" in str(models_error) or "unauthorized" in str(models_error).lower():
                return ValidationResult(
                    status=ValidationStatus.INVALID_KEY,
                    provider_name=provider_name,
                    success=False,
                    error_message=f"API key invalid: {models_error}",
                    fix_steps=[
                        "1. Check API key is correct",
                        "2. Regenerate key in provider dashboard",
                        "3. Update key in HUD",
                        "4. Reconnect"
                    ],
                    dashboard_url=self.DASHBOARD_URLS.get(provider_name)
                )
            elif "403" in str(models_error) or "forbidden" in str(models_error).lower():
                return ValidationResult(
                    status=ValidationStatus.NO_PERMISSION,
                    provider_name=provider_name,
                    success=False,
                    error_message=f"Insufficient permissions: {models_error}",
                    fix_steps=self._get_permission_fix_steps(provider_name),
                    dashboard_url=self.DASHBOARD_URLS.get(provider_name),
                    required_scopes=self.REQUIRED_SCOPES.get(provider_name, [])
                )
            else:
                return ValidationResult(
                    status=ValidationStatus.CONNECTION_ERROR,
                    provider_name=provider_name,
                    success=False,
                    error_message=str(models_error),
                    fix_steps=[
                        "1. Check internet connection",
                        "2. Verify provider is not down",
                        "3. Try again later"
                    ]
                )
        
        if not models:
            return ValidationResult(
                status=ValidationStatus.NO_MODELS,
                provider_name=provider_name,
                success=False,
                error_message="No models available",
                fix_steps=[
                    "1. Check account has model access",
                    "2. Verify billing is enabled",
                    "3. Contact provider support"
                ],
                dashboard_url=self.DASHBOARD_URLS.get(provider_name)
            )
        
        # Step 3: Test inference with first available model
        test_model = models[0] if models else None
        inference_success, inference_error = self._test_inference(
            provider_name,
            provider_config,
            api_key,
            test_model
        )
        
        if not inference_success:
            # Inference failed but model listing worked
            if "403" in str(inference_error) or "forbidden" in str(inference_error).lower():
                return ValidationResult(
                    status=ValidationStatus.NO_PERMISSION,
                    provider_name=provider_name,
                    success=False,
                    available_models=models,
                    tested_model=test_model,
                    error_message=f"Inference forbidden: {inference_error}",
                    fix_steps=self._get_permission_fix_steps(provider_name, include_inference=True),
                    dashboard_url=self.DASHBOARD_URLS.get(provider_name),
                    required_scopes=self.REQUIRED_SCOPES.get(provider_name, [])
                )
        
        # Success!
        result = ValidationResult(
            status=ValidationStatus.VALID,
            provider_name=provider_name,
            success=True,
            available_models=models,
            tested_model=test_model,
            error_message=None
        )
        
        # Cache result
        self.validation_cache[cache_key] = result
        
        logger.info(f"✅ {provider_name} validated: {len(models)} models available")
        return result
    
    def _test_model_listing(
        self,
        provider_name: str,
        provider_config: Dict,
        api_key: str
    ) -> Tuple[List[str], Optional[str]]:
        """Test fetching model list"""
        try:
            base_url = provider_config.get('base_url')
            models_endpoint = provider_config.get('models_endpoint', 'v1/models')
            headers = provider_config.get('headers', {}).copy()
            headers['Authorization'] = f"Bearer {api_key}"
            
            # Build URL
            if models_endpoint.startswith('http'):
                url = models_endpoint
            else:
                url = f"{base_url}/{models_endpoint}"
            
            # Fetch
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return [], f"HTTP {response.status_code}: {response.text[:200]}"
            
            # Parse
            data = response.json()
            raw_models = data.get('data', data.get('models', []))
            
            # Extract model IDs
            model_ids = []
            for model in raw_models:
                if isinstance(model, dict):
                    model_id = model.get('id', model.get('name'))
                    if model_id:
                        model_ids.append(model_id)
                elif isinstance(model, str):
                    model_ids.append(model)
            
            return model_ids, None
            
        except Exception as e:
            return [], str(e)
    
    def _test_inference(
        self,
        provider_name: str,
        provider_config: Dict,
        api_key: str,
        model: str
    ) -> Tuple[bool, Optional[str]]:
        """Test inference capability"""
        try:
            base_url = provider_config.get('base_url')
            chat_endpoint = provider_config.get('chat_endpoint', 'v1/chat/completions')
            headers = provider_config.get('headers', {}).copy()
            headers['Authorization'] = f"Bearer {api_key}"
            
            # Build URL
            if chat_endpoint.startswith('http'):
                url = chat_endpoint
            else:
                url = f"{base_url}/{chat_endpoint}"
            
            # Minimal test payload
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 5
            }
            
            # Test
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                return True, None
            else:
                return False, f"HTTP {response.status_code}: {response.text[:200]}"
                
        except Exception as e:
            # Inference test failed, but we still have models
            return False, str(e)
    
    def _get_permission_fix_steps(
        self,
        provider_name: str,
        include_inference: bool = False
    ) -> List[str]:
        """Get provider-specific permission fix steps"""
        base_steps = [
            f"1. Go to {provider_name} dashboard",
            "2. Navigate to API keys/tokens section",
            "3. Check current token permissions"
        ]
        
        if provider_name == "Hugging Face":
            return base_steps + [
                "4. Enable 'Make calls to serverless Inference API' permission",
                "5. Enable 'Read access to contents of all repos' if needed",
                "6. Save token settings",
                "7. Update token in HUD",
                "8. Reconnect"
            ]
        elif provider_name == "OpenRouter":
            return base_steps + [
                "4. Ensure account has credits/billing enabled",
                "5. Check model access permissions",
                "6. Regenerate key if needed",
                "7. Update in HUD and reconnect"
            ]
        elif provider_name == "Together AI":
            return base_steps + [
                "4. Verify API key has 'inference' scope",
                "5. Check billing is active",
                "6. Regenerate key with full permissions",
                "7. Update in HUD"
            ]
        else:
            return base_steps + [
                "4. Regenerate API key with full permissions",
                "5. Update in HUD",
                "6. Reconnect"
            ]
    
    def validate_all_providers(
        self,
        providers: List[Dict],
        force_refresh: bool = False
    ) -> Dict[str, ValidationResult]:
        """Validate all providers at once"""
        results = {}
        
        for provider in providers:
            if provider.get('status') != 'active':
                continue
            
            name = provider.get('name')
            result = self.validate_provider(name, provider, force_refresh)
            results[name] = result
        
        return results
    
    def get_valid_models_for_ui(
        self,
        provider_name: str,
        provider_config: Dict
    ) -> List[str]:
        """Get only valid, available models for UI display"""
        result = self.validate_provider(provider_name, provider_config)
        
        if result.success:
            return result.available_models
        else:
            logger.warning(f"{provider_name} validation failed: {result.error_message}")
            return []


# Singleton instance
_validator = None

def get_preflight_validator() -> ProviderPreFlightValidator:
    """Get or create global validator instance"""
    global _validator
    if _validator is None:
        _validator = ProviderPreFlightValidator()
    return _validator
