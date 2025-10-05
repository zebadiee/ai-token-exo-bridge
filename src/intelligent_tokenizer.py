#!/usr/bin/env python3
"""
Intelligent Tokenizer & Model Sync System
PhD-level preprocessing and validation for multi-provider AI inference

Features:
- Universal tokenization with fallback strategies
- Real-time token counting and validation
- Model catalog synchronization per provider
- Automatic prompt truncation and formatting
- Provider-specific encoding detection
- Pre-flight validation to prevent API errors
"""

import logging
import tiktoken
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TokenizationResult:
    """Result of tokenization with metadata"""
    tokens: List[int]
    token_count: int
    text: str
    encoding_name: str
    truncated: bool = False
    original_length: int = 0
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "token_count": self.token_count,
            "encoding": self.encoding_name,
            "truncated": self.truncated,
            "original_length": self.original_length,
            "warnings": self.warnings
        }


@dataclass
class ModelInfo:
    """Provider model information"""
    id: str
    name: str
    provider: str
    context_length: int = 4096
    supports_streaming: bool = False
    supports_functions: bool = False
    cost_per_1k_prompt: float = 0.0
    cost_per_1k_completion: float = 0.0
    encoding: str = "cl100k_base"  # Default tiktoken encoding
    last_synced: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "context_length": self.context_length,
            "supports_streaming": self.supports_streaming,
            "supports_functions": self.supports_functions,
            "cost_per_1k_prompt": self.cost_per_1k_prompt,
            "cost_per_1k_completion": self.cost_per_1k_completion,
            "encoding": self.encoding,
            "last_synced": self.last_synced.isoformat() if self.last_synced else None
        }


class IntelligentTokenizer:
    """
    Universal tokenizer with provider-specific optimizations
    
    Handles:
    - Multiple encoding schemes (tiktoken, sentencepiece, etc.)
    - Automatic fallback strategies
    - Token counting with caching
    - Prompt truncation and formatting
    - Pre-flight validation
    """
    
    def __init__(self):
        """Initialize tokenizer with common encodings"""
        self.encodings = {}
        self.token_cache = {}
        
        # Load common tiktoken encodings
        common_encodings = [
            "cl100k_base",  # GPT-4, GPT-3.5-turbo
            "p50k_base",    # Codex
            "r50k_base",    # GPT-3 (davinci)
        ]
        
        for enc_name in common_encodings:
            try:
                self.encodings[enc_name] = tiktoken.get_encoding(enc_name)
                logger.info(f"Loaded encoding: {enc_name}")
            except Exception as e:
                logger.warning(f"Could not load encoding {enc_name}: {e}")
        
        # Default encoding
        self.default_encoding = self.encodings.get("cl100k_base")
    
    def count_tokens(
        self, 
        text: str, 
        encoding_name: str = "cl100k_base",
        model: str = None
    ) -> TokenizationResult:
        """
        Count tokens in text with automatic encoding selection
        
        Args:
            text: Input text
            encoding_name: Encoding to use
            model: Optional model name for auto-detection
            
        Returns:
            TokenizationResult with detailed info
        """
        # Auto-detect encoding from model if provided
        if model:
            encoding_name = self._detect_encoding_for_model(model)
        
        # Get encoder
        encoder = self.encodings.get(encoding_name, self.default_encoding)
        
        if not encoder:
            logger.error("No encoding available, using fallback")
            return self._fallback_tokenize(text)
        
        try:
            # Tokenize
            tokens = encoder.encode(text)
            
            return TokenizationResult(
                tokens=tokens,
                token_count=len(tokens),
                text=text,
                encoding_name=encoding_name,
                original_length=len(text)
            )
            
        except Exception as e:
            logger.error(f"Tokenization failed: {e}")
            return self._fallback_tokenize(text)
    
    def truncate_to_limit(
        self,
        text: str,
        max_tokens: int,
        encoding_name: str = "cl100k_base",
        model: str = None,
        strategy: str = "end"  # "end", "middle", "start"
    ) -> TokenizationResult:
        """
        Truncate text to token limit with various strategies
        
        Args:
            text: Input text
            max_tokens: Maximum token count
            encoding_name: Encoding to use
            model: Optional model name
            strategy: Truncation strategy
            
        Returns:
            TokenizationResult with truncated text
        """
        # First, count tokens
        result = self.count_tokens(text, encoding_name, model)
        
        if result.token_count <= max_tokens:
            # No truncation needed
            return result
        
        # Get encoder
        if model:
            encoding_name = self._detect_encoding_for_model(model)
        
        encoder = self.encodings.get(encoding_name, self.default_encoding)
        
        if not encoder:
            return self._fallback_truncate(text, max_tokens)
        
        # Tokenize
        tokens = encoder.encode(text)
        original_count = len(tokens)
        
        # Apply truncation strategy
        if strategy == "end":
            truncated_tokens = tokens[:max_tokens]
        elif strategy == "start":
            truncated_tokens = tokens[-max_tokens:]
        elif strategy == "middle":
            # Keep start and end, remove middle
            half = max_tokens // 2
            truncated_tokens = tokens[:half] + tokens[-half:]
        else:
            truncated_tokens = tokens[:max_tokens]
        
        # Decode back to text
        truncated_text = encoder.decode(truncated_tokens)
        
        return TokenizationResult(
            tokens=truncated_tokens,
            token_count=len(truncated_tokens),
            text=truncated_text,
            encoding_name=encoding_name,
            truncated=True,
            original_length=original_count,
            warnings=[f"Truncated from {original_count} to {len(truncated_tokens)} tokens using '{strategy}' strategy"]
        )
    
    def validate_for_model(
        self,
        text: str,
        model_info: ModelInfo,
        reserve_tokens: int = 512  # Reserve for completion
    ) -> Tuple[bool, str, TokenizationResult]:
        """
        Validate text for a specific model
        
        Args:
            text: Input text
            model_info: Model information
            reserve_tokens: Tokens to reserve for response
            
        Returns:
            Tuple of (is_valid, error_message, tokenization_result)
        """
        result = self.count_tokens(text, model_info.encoding, model_info.id)
        
        max_allowed = model_info.context_length - reserve_tokens
        
        if result.token_count > max_allowed:
            error_msg = (
                f"Input too long: {result.token_count} tokens exceeds "
                f"limit of {max_allowed} (context: {model_info.context_length}, "
                f"reserved: {reserve_tokens})"
            )
            return False, error_msg, result
        
        return True, "", result
    
    def format_messages_with_tokens(
        self,
        messages: List[Dict[str, str]],
        model: str = None
    ) -> Tuple[List[Dict], int, List[str]]:
        """
        Format chat messages and count total tokens
        
        Args:
            messages: List of message dicts
            model: Optional model name
            
        Returns:
            Tuple of (messages, total_tokens, warnings)
        """
        total_tokens = 0
        warnings = []
        formatted_messages = []
        
        for msg in messages:
            content = msg.get("content", "")
            role = msg.get("role", "user")
            
            # Count tokens for this message
            result = self.count_tokens(content, model=model)
            total_tokens += result.token_count
            
            # Add role tokens (approximate)
            total_tokens += 4  # <|start|>role<|message|>content<|end|>
            
            formatted_messages.append({
                "role": role,
                "content": content,
                "token_count": result.token_count
            })
        
        # Add final assistant token
        total_tokens += 3
        
        return formatted_messages, total_tokens, warnings
    
    def _detect_encoding_for_model(self, model: str) -> str:
        """Detect best encoding for model"""
        model_lower = model.lower()
        
        # GPT-4 and GPT-3.5
        if "gpt-4" in model_lower or "gpt-3.5" in model_lower:
            return "cl100k_base"
        
        # GPT-3
        if "davinci" in model_lower or "curie" in model_lower or "babbage" in model_lower:
            return "r50k_base"
        
        # Codex
        if "code" in model_lower:
            return "p50k_base"
        
        # Default
        return "cl100k_base"
    
    def _fallback_tokenize(self, text: str) -> TokenizationResult:
        """Fallback tokenization using simple word splitting"""
        words = text.split()
        # Rough estimate: 1 token ≈ 0.75 words
        estimated_tokens = int(len(words) / 0.75)
        
        return TokenizationResult(
            tokens=[],
            token_count=estimated_tokens,
            text=text,
            encoding_name="fallback_wordcount",
            original_length=len(text),
            warnings=["Using fallback word-count estimation"]
        )
    
    def _fallback_truncate(self, text: str, max_tokens: int) -> TokenizationResult:
        """Fallback truncation using character count"""
        # Rough estimate: 1 token ≈ 4 characters
        max_chars = max_tokens * 4
        
        if len(text) <= max_chars:
            return self._fallback_tokenize(text)
        
        truncated = text[:max_chars]
        
        return TokenizationResult(
            tokens=[],
            token_count=max_tokens,
            text=truncated,
            encoding_name="fallback_charcount",
            truncated=True,
            original_length=len(text),
            warnings=["Using fallback character-based truncation"]
        )


class ModelCatalogSync:
    """
    Synchronizes and maintains model catalogs for all providers
    
    Features:
    - Auto-fetch model lists from providers
    - Cache with TTL
    - Model capability detection
    - Context length mapping
    - Cost estimation
    """
    
    def __init__(self, config_path: str = None):
        """Initialize model catalog"""
        self.config_path = config_path or str(Path.home() / ".token_manager_config.json")
        self.catalog_path = str(Path.home() / ".model_catalog.json")
        self.models: Dict[str, List[ModelInfo]] = {}
        self.last_sync: Dict[str, datetime] = {}
        self.sync_ttl = 3600  # 1 hour cache
        
        # Load cached catalog
        self._load_catalog()
    
    def sync_provider_models(
        self,
        provider_name: str,
        provider_config: Dict,
        force: bool = False
    ) -> Tuple[List[ModelInfo], Optional[str]]:
        """
        Sync models for a specific provider
        
        Args:
            provider_name: Name of provider
            provider_config: Provider configuration
            force: Force refresh even if cached
            
        Returns:
            Tuple of (models, error)
        """
        # Check cache
        if not force and provider_name in self.last_sync:
            age = (datetime.now() - self.last_sync[provider_name]).total_seconds()
            if age < self.sync_ttl:
                logger.info(f"Using cached models for {provider_name}")
                return self.models.get(provider_name, []), None
        
        logger.info(f"Syncing models for {provider_name}...")
        
        try:
            import requests
            
            # Build request
            base_url = provider_config.get('base_url')
            models_endpoint = provider_config.get('models_endpoint', 'v1/models')
            
            # Get API key
            api_key = provider_config.get('api_key') or provider_config.get('api_key_encrypted')
            if not api_key:
                return [], f"No API key for {provider_name}"
            
            # Build headers
            headers = provider_config.get('headers', {}).copy()
            headers['Authorization'] = f"Bearer {api_key}"
            
            # URL
            if models_endpoint.startswith('http'):
                url = models_endpoint
            else:
                url = f"{base_url}/{models_endpoint}"
            
            # Fetch
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.error(f"{provider_name} model sync failed: {error_msg}")
                return [], error_msg
            
            # Parse
            data = response.json()
            raw_models = data.get('data', data.get('models', []))
            
            # Convert to ModelInfo
            models = []
            for raw_model in raw_models:
                model_info = self._parse_model_info(raw_model, provider_name)
                if model_info:
                    models.append(model_info)
            
            # Cache
            self.models[provider_name] = models
            self.last_sync[provider_name] = datetime.now()
            self._save_catalog()
            
            logger.info(f"Synced {len(models)} models for {provider_name}")
            return models, None
            
        except Exception as e:
            error_msg = f"Model sync failed: {e}"
            logger.error(f"{provider_name}: {error_msg}")
            return [], error_msg
    
    def get_model_info(self, model_id: str, provider: str = None) -> Optional[ModelInfo]:
        """Get model information by ID"""
        if provider and provider in self.models:
            for model in self.models[provider]:
                if model.id == model_id:
                    return model
        else:
            # Search all providers
            for provider_models in self.models.values():
                for model in provider_models:
                    if model.id == model_id:
                        return model
        return None
    
    def get_models_for_provider(self, provider: str) -> List[ModelInfo]:
        """Get all models for a provider"""
        return self.models.get(provider, [])
    
    def get_all_models(self) -> List[ModelInfo]:
        """Get all models across providers"""
        all_models = []
        for models in self.models.values():
            all_models.extend(models)
        return all_models
    
    def find_alternative_models(
        self,
        model_id: str,
        provider: str = None,
        min_context: int = 4096
    ) -> List[ModelInfo]:
        """Find alternative models similar to the requested one"""
        alternatives = []
        
        # Get original model info
        original = self.get_model_info(model_id, provider)
        
        # Search criteria
        for provider_models in self.models.values():
            for model in provider_models:
                # Skip if same model
                if model.id == model_id:
                    continue
                
                # Check context length
                if model.context_length < min_context:
                    continue
                
                # Similarity scoring (basic)
                score = 0
                if original:
                    # Same provider
                    if model.provider == original.provider:
                        score += 10
                    # Similar name
                    if any(word in model.id.lower() for word in original.id.lower().split('-')):
                        score += 5
                    # Similar context
                    if abs(model.context_length - original.context_length) < 2000:
                        score += 3
                
                alternatives.append((score, model))
        
        # Sort by score
        alternatives.sort(key=lambda x: x[0], reverse=True)
        
        return [model for score, model in alternatives[:5]]
    
    def _parse_model_info(self, raw_model: Any, provider: str) -> Optional[ModelInfo]:
        """Parse raw model data into ModelInfo"""
        try:
            if isinstance(raw_model, dict):
                model_id = raw_model.get('id', raw_model.get('name'))
                
                # Extract context length
                context_length = 4096  # Default
                if 'context_length' in raw_model:
                    context_length = raw_model['context_length']
                elif 'max_tokens' in raw_model:
                    context_length = raw_model['max_tokens']
                elif 'context_window' in raw_model:
                    context_length = raw_model['context_window']
                elif '32k' in model_id.lower():
                    context_length = 32768
                elif '16k' in model_id.lower():
                    context_length = 16384
                elif '8k' in model_id.lower():
                    context_length = 8192
                
                # Extract pricing
                pricing = raw_model.get('pricing', {})
                prompt_cost = float(pricing.get('prompt', 0)) if pricing else 0
                completion_cost = float(pricing.get('completion', 0)) if pricing else 0
                
                # Detect encoding
                encoding = "cl100k_base"  # Default for modern models
                if "gpt-3" in model_id.lower() and "turbo" not in model_id.lower():
                    encoding = "r50k_base"
                elif "code" in model_id.lower():
                    encoding = "p50k_base"
                
                return ModelInfo(
                    id=model_id,
                    name=raw_model.get('name', model_id),
                    provider=provider,
                    context_length=context_length,
                    supports_streaming=raw_model.get('supports_streaming', False),
                    supports_functions=raw_model.get('supports_functions', False),
                    cost_per_1k_prompt=prompt_cost,
                    cost_per_1k_completion=completion_cost,
                    encoding=encoding,
                    last_synced=datetime.now()
                )
            
        except Exception as e:
            logger.error(f"Failed to parse model: {e}")
        
        return None
    
    def _load_catalog(self):
        """Load cached catalog from disk"""
        try:
            if Path(self.catalog_path).exists():
                with open(self.catalog_path, 'r') as f:
                    data = json.load(f)
                
                for provider, models_data in data.get('models', {}).items():
                    models = []
                    for model_data in models_data:
                        # Reconstruct ModelInfo
                        model_data['last_synced'] = datetime.fromisoformat(model_data['last_synced']) if model_data.get('last_synced') else None
                        models.append(ModelInfo(**model_data))
                    self.models[provider] = models
                
                for provider, sync_time in data.get('last_sync', {}).items():
                    self.last_sync[provider] = datetime.fromisoformat(sync_time)
                
                logger.info(f"Loaded model catalog with {sum(len(m) for m in self.models.values())} models")
        except Exception as e:
            logger.error(f"Failed to load catalog: {e}")
    
    def _save_catalog(self):
        """Save catalog to disk"""
        try:
            data = {
                'models': {
                    provider: [model.to_dict() for model in models]
                    for provider, models in self.models.items()
                },
                'last_sync': {
                    provider: sync_time.isoformat()
                    for provider, sync_time in self.last_sync.items()
                }
            }
            
            with open(self.catalog_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save catalog: {e}")


# Singleton instances
_tokenizer = None
_catalog = None

def get_tokenizer() -> IntelligentTokenizer:
    """Get or create global tokenizer instance"""
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = IntelligentTokenizer()
    return _tokenizer

def get_model_catalog() -> ModelCatalogSync:
    """Get or create global model catalog instance"""
    global _catalog
    if _catalog is None:
        _catalog = ModelCatalogSync()
    return _catalog
