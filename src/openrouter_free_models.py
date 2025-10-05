#!/usr/bin/env python3
"""
OpenRouter Free Models Filter

Filters and caches only free (zero-cost) models from OpenRouter.
Ensures no accidental charges by blocking paid model selection.

Features:
- Fetches models from OpenRouter API
- Filters for $0.00 cost models only
- Caches results with TTL
- Blocks paid model requests
- UI integration helpers
"""

import requests
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about an OpenRouter model"""
    id: str
    name: str
    pricing: Dict[str, float]
    context_length: int
    is_free: bool
    description: Optional[str] = None
    
    @property
    def cost_per_1k_prompt(self) -> float:
        """Get prompt cost per 1K tokens"""
        return self.pricing.get('prompt', 0.0)
    
    @property
    def cost_per_1k_completion(self) -> float:
        """Get completion cost per 1K tokens"""
        return self.pricing.get('completion', 0.0)
    
    @property
    def is_truly_free(self) -> bool:
        """Check if model is truly free (both prompt and completion are $0)"""
        return self.cost_per_1k_prompt == 0.0 and self.cost_per_1k_completion == 0.0
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'pricing': self.pricing,
            'context_length': self.context_length,
            'is_free': self.is_free,
            'description': self.description
        }


class OpenRouterFreeModelsFilter:
    """
    Filter and manage free-only models from OpenRouter
    
    Ensures zero-cost operation by:
    1. Fetching all models from OpenRouter API
    2. Filtering for $0.00 pricing only
    3. Caching results with TTL (24 hours)
    4. Blocking paid model selection
    5. Providing UI-ready lists
    """
    
    OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
    CACHE_TTL_HOURS = 24
    
    def __init__(self, api_key: str, cache_path: Optional[str] = None):
        """
        Initialize free models filter
        
        Args:
            api_key: OpenRouter API key
            cache_path: Path to cache file (default: ~/.openrouter_free_models.json)
        """
        self.api_key = api_key
        self.cache_path = cache_path or str(Path.home() / ".openrouter_free_models.json")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "spiral-codex-hud",
            "X-Title": "Spiral Codex HUD - Free Models Only"
        }
        self.free_models: List[ModelInfo] = []
        self.last_fetch: Optional[datetime] = None
    
    def fetch_all_models(self) -> List[Dict]:
        """
        Fetch all available models from OpenRouter API
        
        Returns:
            List of model dictionaries from API
        """
        try:
            logger.info("Fetching models from OpenRouter API...")
            response = requests.get(
                f"{self.OPENROUTER_API_BASE}/models",
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch models: HTTP {response.status_code}")
                return []
            
            data = response.json()
            models = data.get('data', [])
            
            logger.info(f"Fetched {len(models)} total models from OpenRouter")
            return models
            
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return []
    
    def filter_free_models(self, all_models: List[Dict]) -> List[ModelInfo]:
        """
        Filter models to only free (zero-cost) options
        
        Args:
            all_models: All models from API
            
        Returns:
            List of ModelInfo objects for free models only
        """
        free_models = []
        
        for model_data in all_models:
            try:
                model_id = model_data.get('id', '')
                name = model_data.get('name', model_id)
                pricing = model_data.get('pricing', {})
                context_length = model_data.get('context_length', 0)
                description = model_data.get('description', '')
                
                # Extract pricing info
                prompt_cost = float(pricing.get('prompt', '0').replace('$', ''))
                completion_cost = float(pricing.get('completion', '0').replace('$', ''))
                
                # Check if truly free
                is_free = (prompt_cost == 0.0 and completion_cost == 0.0)
                
                if is_free:
                    model_info = ModelInfo(
                        id=model_id,
                        name=name,
                        pricing={'prompt': prompt_cost, 'completion': completion_cost},
                        context_length=context_length,
                        is_free=True,
                        description=description
                    )
                    free_models.append(model_info)
                    
            except Exception as e:
                logger.warning(f"Failed to parse model {model_data.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Found {len(free_models)} free models (from {len(all_models)} total)")
        return free_models
    
    def get_free_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """
        Get cached or fetch fresh list of free models
        
        Args:
            force_refresh: Force fetch from API even if cache is valid
            
        Returns:
            List of free ModelInfo objects
        """
        # Check cache validity
        if not force_refresh and self._is_cache_valid():
            cached = self._load_cache()
            if cached:
                logger.info(f"Using cached free models: {len(cached)} models")
                self.free_models = cached
                return cached
        
        # Fetch fresh from API
        logger.info("Fetching fresh free models list...")
        all_models = self.fetch_all_models()
        
        if not all_models:
            logger.warning("No models fetched, using cache if available")
            cached = self._load_cache()
            if cached:
                self.free_models = cached
                return cached
            return []
        
        # Filter for free only
        free_models = self.filter_free_models(all_models)
        
        # Cache results
        self._save_cache(free_models)
        self.free_models = free_models
        self.last_fetch = datetime.now()
        
        return free_models
    
    def is_model_free(self, model_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a specific model is free
        
        Args:
            model_id: Model ID to check
            
        Returns:
            (is_free, error_message)
        """
        # Ensure we have free models list
        if not self.free_models:
            self.get_free_models()
        
        # Check if model is in free list
        for model in self.free_models:
            if model.id == model_id:
                return True, None
        
        # Not in free list - it's paid
        return False, (
            f"Model '{model_id}' is not free. "
            f"Only zero-cost models are allowed. "
            f"Choose from {len(self.free_models)} available free models."
        )
    
    def block_paid_model(self, model_id: str) -> bool:
        """
        Block a paid model from being used
        
        Args:
            model_id: Model ID to check
            
        Returns:
            True if model is free (allowed), False if paid (blocked)
        """
        is_free, error = self.is_model_free(model_id)
        
        if not is_free:
            logger.warning(f"BLOCKED paid model request: {model_id}")
            logger.warning(f"Reason: {error}")
            return False
        
        return True
    
    def get_ui_model_list(self) -> List[Dict[str, str]]:
        """
        Get model list formatted for UI display
        
        Returns:
            List of dicts with 'id', 'display_name', 'context' for UI
        """
        models = self.get_free_models()
        
        return [
            {
                'id': model.id,
                'display_name': f"{model.name} (FREE - {model.context_length:,} tokens)",
                'context': model.context_length,
                'description': model.description or "Free model"
            }
            for model in models
        ]
    
    def get_model_ids_only(self) -> List[str]:
        """Get just the model IDs for simple selection"""
        models = self.get_free_models()
        return [model.id for model in models]
    
    def get_free_models_summary(self) -> Dict:
        """Get summary statistics about free models"""
        models = self.get_free_models()
        
        if not models:
            return {
                'count': 0,
                'total_context': 0,
                'average_context': 0,
                'cache_age': 'No cache'
            }
        
        total_context = sum(m.context_length for m in models)
        
        return {
            'count': len(models),
            'total_context': total_context,
            'average_context': total_context // len(models) if models else 0,
            'cache_age': self._get_cache_age(),
            'last_refresh': self.last_fetch.isoformat() if self.last_fetch else 'Never'
        }
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid based on TTL"""
        cache_path = Path(self.cache_path)
        
        if not cache_path.exists():
            return False
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            cached_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
            age = datetime.now() - cached_time
            
            return age < timedelta(hours=self.CACHE_TTL_HOURS)
            
        except Exception as e:
            logger.warning(f"Cache validation failed: {e}")
            return False
    
    def _load_cache(self) -> Optional[List[ModelInfo]]:
        """Load models from cache file"""
        cache_path = Path(self.cache_path)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            models_data = cache_data.get('models', [])
            models = [
                ModelInfo(
                    id=m['id'],
                    name=m['name'],
                    pricing=m['pricing'],
                    context_length=m['context_length'],
                    is_free=m['is_free'],
                    description=m.get('description')
                )
                for m in models_data
            ]
            
            self.last_fetch = datetime.fromisoformat(cache_data.get('timestamp', ''))
            
            return models
            
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return None
    
    def _save_cache(self, models: List[ModelInfo]):
        """Save models to cache file"""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'ttl_hours': self.CACHE_TTL_HOURS,
                'models': [m.to_dict() for m in models]
            }
            
            with open(self.cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"Cached {len(models)} free models to {self.cache_path}")
            
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _get_cache_age(self) -> str:
        """Get human-readable cache age"""
        if not self.last_fetch:
            return "No cache"
        
        age = datetime.now() - self.last_fetch
        
        if age.total_seconds() < 3600:
            return f"{int(age.total_seconds() / 60)} minutes ago"
        elif age.total_seconds() < 86400:
            return f"{int(age.total_seconds() / 3600)} hours ago"
        else:
            return f"{age.days} days ago"
    
    def print_summary(self):
        """Print summary of free models"""
        summary = self.get_free_models_summary()
        
        print("=" * 70)
        print("OPENROUTER FREE MODELS SUMMARY")
        print("=" * 70)
        print()
        print(f"Free Models Available: {summary['count']}")
        print(f"Average Context Length: {summary['average_context']:,} tokens")
        print(f"Cache Age: {summary['cache_age']}")
        print()
        
        if self.free_models:
            print("Available Free Models:")
            print("-" * 70)
            for model in sorted(self.free_models, key=lambda m: m.name):
                print(f"  • {model.name}")
                print(f"    ID: {model.id}")
                print(f"    Context: {model.context_length:,} tokens")
                print(f"    Cost: $0.00 (FREE)")
                print()
        
        print("=" * 70)
        print()
        print("All listed models have $0.00 cost for both prompt and completion.")
        print("No charges will be incurred when using these models.")
        print()


# Singleton instance
_free_models_filter: Optional[OpenRouterFreeModelsFilter] = None


def get_free_models_filter(api_key: str) -> OpenRouterFreeModelsFilter:
    """Get or create global free models filter instance"""
    global _free_models_filter
    if _free_models_filter is None:
        _free_models_filter = OpenRouterFreeModelsFilter(api_key)
    return _free_models_filter


# Streamlit integration
def streamlit_free_model_selector(api_key: str, key: str = "free_model_select"):
    """
    Streamlit widget for free model selection
    
    Args:
        api_key: OpenRouter API key
        key: Streamlit widget key
        
    Returns:
        Selected model ID or None
    """
    import streamlit as st
    
    filter_instance = get_free_models_filter(api_key)
    
    # Get free models
    ui_models = filter_instance.get_ui_model_list()
    
    if not ui_models:
        st.error("❌ No free models available")
        st.info("Check your OpenRouter API key and internet connection")
        return None
    
    # Show summary
    summary = filter_instance.get_free_models_summary()
    st.success(f"✅ {summary['count']} FREE models available (zero cost)")
    st.caption(f"Last refreshed: {summary['cache_age']}")
    
    # Model selector
    selected_display = st.selectbox(
        "Select Free Model (No Charges)",
        options=[m['display_name'] for m in ui_models],
        key=key,
        help="Only zero-cost models shown. No billing risk."
    )
    
    # Find selected model ID
    if selected_display:
        for model in ui_models:
            if model['display_name'] == selected_display:
                
                # Show model info
                with st.expander("ℹ️ Model Details"):
                    st.write(f"**ID:** {model['id']}")
                    st.write(f"**Context:** {model['context']:,} tokens")
                    st.write(f"**Cost:** $0.00 (FREE)")
                    st.write(f"**Description:** {model['description']}")
                
                return model['id']
    
    return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python openrouter_free_models.py YOUR_API_KEY")
        print()
        print("Example:")
        print("  python openrouter_free_models.py sk-or-v1-...")
        sys.exit(1)
    
    api_key = sys.argv[1]
    
    # Create filter and fetch models
    filter_instance = OpenRouterFreeModelsFilter(api_key)
    models = filter_instance.get_free_models(force_refresh=True)
    
    # Print summary
    filter_instance.print_summary()
