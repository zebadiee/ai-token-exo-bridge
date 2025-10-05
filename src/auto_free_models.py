#!/usr/bin/env python3
"""
Auto Free Models Highlighter and Filter

Automatically detects free models from providers and highlights them in UI.

Features:
- Auto-fetch and filter free models
- Visual "FREE" badges in UI
- Lock out paid models by default
- Opt-in for paid model access
"""

import requests
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelEntry:
    """Model entry with pricing info"""
    id: str
    name: str
    is_free: bool
    prompt_cost: float
    completion_cost: float
    context_length: int
    provider: str
    display_name: str
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'is_free': self.is_free,
            'prompt_cost': self.prompt_cost,
            'completion_cost': self.completion_cost,
            'context_length': self.context_length,
            'provider': self.provider,
            'display_name': self.display_name
        }


class FreeModelsHighlighter:
    """
    Auto-detect and highlight free models
    
    Features:
    - Fetches models with pricing
    - Filters for free ($0.00) models
    - Adds visual indicators
    - Paid model lock-out option
    """
    
    def __init__(self):
        """Initialize highlighter"""
        self.show_paid_models = False  # Default: free only
        self.free_models: List[ModelEntry] = []
        self.paid_models: List[ModelEntry] = []
    
    def fetch_and_categorize_models(
        self,
        provider_name: str,
        api_key: str,
        api_base_url: str
    ) -> Tuple[List[ModelEntry], List[ModelEntry]]:
        """
        Fetch models and categorize as free/paid
        
        Args:
            provider_name: Name of provider
            api_key: API key
            api_base_url: Base URL for API
            
        Returns:
            (free_models, paid_models)
        """
        logger.info(f"Fetching models from {provider_name}...")
        
        try:
            # Fetch models
            headers = {
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "spiral-codex-hud",
                "X-Title": "Spiral Codex HUD"
            }
            
            response = requests.get(
                f"{api_base_url}/v1/models",
                headers=headers,
                timeout=15
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch models: HTTP {response.status_code}")
                return [], []
            
            data = response.json()
            models_data = data.get('data', [])
            
            # Categorize
            free_models = []
            paid_models = []
            
            for model_data in models_data:
                model_entry = self._parse_model(model_data, provider_name)
                
                if model_entry.is_free:
                    free_models.append(model_entry)
                else:
                    paid_models.append(model_entry)
            
            self.free_models = free_models
            self.paid_models = paid_models
            
            logger.info(
                f"Categorized: {len(free_models)} free, {len(paid_models)} paid"
            )
            
            return free_models, paid_models
            
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return [], []
    
    def _parse_model(self, model_data: Dict, provider: str) -> ModelEntry:
        """Parse model data and extract pricing"""
        model_id = model_data.get('id', 'unknown')
        name = model_data.get('name', model_id)
        context_length = model_data.get('context_length', 0)
        
        # Extract pricing
        pricing = model_data.get('pricing', {})
        
        try:
            prompt_cost = float(str(pricing.get('prompt', '0')).replace('$', ''))
            completion_cost = float(str(pricing.get('completion', '0')).replace('$', ''))
        except:
            # Unknown pricing = treat as paid
            prompt_cost = float('inf')
            completion_cost = float('inf')
        
        is_free = (prompt_cost == 0.0 and completion_cost == 0.0)
        
        # Check for :free label
        has_free_label = ':free' in model_id.lower()
        
        # Create display name with badge
        if is_free or has_free_label:
            display_name = f"✅ FREE - {name} ({context_length:,} tokens)"
        else:
            display_name = f"💰 ${prompt_cost:.6f} - {name} ({context_length:,} tokens)"
        
        return ModelEntry(
            id=model_id,
            name=name,
            is_free=is_free or has_free_label,
            prompt_cost=prompt_cost,
            completion_cost=completion_cost,
            context_length=context_length,
            provider=provider,
            display_name=display_name
        )
    
    def get_models_for_ui(self, include_paid: bool = False) -> List[ModelEntry]:
        """
        Get models for UI display
        
        Args:
            include_paid: Whether to include paid models
            
        Returns:
            List of models to show
        """
        if include_paid or self.show_paid_models:
            # Show all, but free first
            return self.free_models + self.paid_models
        else:
            # Show only free
            return self.free_models
    
    def get_model_display_names(self, include_paid: bool = False) -> List[str]:
        """Get list of display names for dropdown"""
        models = self.get_models_for_ui(include_paid)
        return [m.display_name for m in models]
    
    def get_model_by_display_name(self, display_name: str) -> Optional[ModelEntry]:
        """Get model entry by display name"""
        all_models = self.free_models + self.paid_models
        
        for model in all_models:
            if model.display_name == display_name:
                return model
        
        return None
    
    def is_model_allowed(self, model_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if model selection is allowed
        
        Args:
            model_id: Model ID to check
            
        Returns:
            (is_allowed, error_message)
        """
        # Check if it's in free models
        for model in self.free_models:
            if model.id == model_id:
                return True, None
        
        # Check if it's paid
        for model in self.paid_models:
            if model.id == model_id:
                if self.show_paid_models:
                    return True, None
                else:
                    return False, (
                        f"Model '{model_id}' is not free. "
                        f"Enable 'Show Paid Models' to use paid models. "
                        f"Cost: ${model.prompt_cost:.6f} prompt, ${model.completion_cost:.6f} completion"
                    )
        
        # Unknown model
        return False, f"Model '{model_id}' not found in available models"
    
    def get_free_model_summary(self) -> Dict:
        """Get summary of free models"""
        if not self.free_models:
            return {
                'count': 0,
                'total_context': 0,
                'average_context': 0,
                'top_models': []
            }
        
        total_context = sum(m.context_length for m in self.free_models)
        
        # Get top 5 by context length
        top_models = sorted(
            self.free_models,
            key=lambda m: m.context_length,
            reverse=True
        )[:5]
        
        return {
            'count': len(self.free_models),
            'total_context': total_context,
            'average_context': total_context // len(self.free_models),
            'top_models': [m.to_dict() for m in top_models]
        }


# Streamlit UI Integration
def streamlit_free_models_selector(
    provider_name: str,
    api_key: str,
    api_base_url: str,
    highlighter: Optional[FreeModelsHighlighter] = None,
    key: str = "free_model_select"
) -> Optional[str]:
    """
    Streamlit widget for free models selection with highlighting
    
    Args:
        provider_name: Provider name
        api_key: API key
        api_base_url: API base URL
        highlighter: Optional highlighter instance
        key: Streamlit widget key
        
    Returns:
        Selected model ID or None
    """
    import streamlit as st
    
    # Get or create highlighter
    if highlighter is None:
        if f'{provider_name}_highlighter' not in st.session_state:
            st.session_state[f'{provider_name}_highlighter'] = FreeModelsHighlighter()
        highlighter = st.session_state[f'{provider_name}_highlighter']
    
    # Fetch models if needed
    if not highlighter.free_models and not highlighter.paid_models:
        with st.spinner(f"Loading {provider_name} models..."):
            free, paid = highlighter.fetch_and_categorize_models(
                provider_name,
                api_key,
                api_base_url
            )
    
    # Show summary
    summary = highlighter.get_free_model_summary()
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.metric("Free Models", summary['count'])
    
    with col2:
        st.metric("Paid Models", len(highlighter.paid_models))
    
    with col3:
        # Toggle for paid models
        show_paid = st.checkbox(
            "Show Paid",
            value=highlighter.show_paid_models,
            key=f"{key}_show_paid",
            help="Enable to see paid models (charges may apply)"
        )
        highlighter.show_paid_models = show_paid
    
    # Model selector
    models = highlighter.get_models_for_ui(include_paid=show_paid)
    
    if not models:
        st.error(f"❌ No models available for {provider_name}")
        return None
    
    # Show selector with badges
    selected_display = st.selectbox(
        f"Select Model ({len(models)} available)",
        options=[m.display_name for m in models],
        key=key,
        help="✅ = Free ($0.00) | 💰 = Paid (charges apply)"
    )
    
    # Get selected model
    selected_model = highlighter.get_model_by_display_name(selected_display)
    
    if selected_model:
        # Show model details
        with st.expander("ℹ️ Model Details"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**ID:** {selected_model.id}")
                st.write(f"**Provider:** {selected_model.provider}")
                st.write(f"**Context:** {selected_model.context_length:,} tokens")
            
            with col2:
                if selected_model.is_free:
                    st.success("**Cost:** $0.00 (FREE)")
                else:
                    st.warning(f"**Prompt Cost:** ${selected_model.prompt_cost:.6f}/1K")
                    st.warning(f"**Completion Cost:** ${selected_model.completion_cost:.6f}/1K")
        
        # Validate selection
        allowed, error = highlighter.is_model_allowed(selected_model.id)
        
        if not allowed:
            st.error(f"❌ {error}")
            return None
        
        return selected_model.id
    
    return None


# Standalone test
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python auto_free_models.py OPENROUTER_API_KEY")
        sys.exit(1)
    
    api_key = sys.argv[1]
    
    highlighter = FreeModelsHighlighter()
    
    print("🔍 Fetching models from OpenRouter...")
    free, paid = highlighter.fetch_and_categorize_models(
        "OpenRouter",
        api_key,
        "https://openrouter.ai/api"
    )
    
    print(f"\n✅ Free Models ({len(free)}):")
    for model in free[:10]:  # Show first 10
        print(f"  {model.display_name}")
    
    print(f"\n💰 Paid Models ({len(paid)}):")
    for model in paid[:5]:  # Show first 5
        print(f"  {model.display_name}")
    
    summary = highlighter.get_free_model_summary()
    print(f"\n📊 Summary:")
    print(f"  Total Free: {summary['count']}")
    print(f"  Avg Context: {summary['average_context']:,} tokens")
