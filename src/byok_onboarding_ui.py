#!/usr/bin/env python3
"""
BYOK Onboarding UI Components for Streamlit

Guided onboarding flows with provider ratings, trust signals, and
step-by-step setup instructions for Bring Your Own Key providers.
"""

import streamlit as st
from typing import Optional, Dict, List
from datetime import datetime
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from byok_provider_registry import (
    BYOKProviderRegistry,
    ProviderRating,
    ProviderDifficulty,
    ProviderStatus,
    get_registry
)


def render_trust_badge(provider: ProviderRating) -> str:
    """Render visual trust badge"""
    trust = provider.get_trust_score()
    
    if trust >= 85:
        return "🏆 Highly Trusted"
    elif trust >= 70:
        return "✅ Trusted"
    elif trust >= 50:
        return "⚠️ Use Caution"
    else:
        return "❌ Not Recommended"


def render_provider_card(provider: ProviderRating, expanded: bool = False):
    """Render a provider card with ratings and info"""
    
    trust_score = provider.get_trust_score()
    rec_level = provider.get_recommendation_level()
    
    # Main container
    with st.container():
        # Header row
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"### {provider.provider_name}")
            st.caption(provider.description)
        
        with col2:
            st.metric("Trust Score", f"{trust_score}/100")
        
        with col3:
            st.metric("Users", f"{provider.active_users:,}")
        
        # Rating row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            stars = "⭐" * int(provider.star_rating)
            st.write(f"{stars} {provider.star_rating}/5")
        
        with col2:
            st.write(f"✅ {provider.success_rate:.1f}% success")
        
        with col3:
            difficulty_emoji = {
                "easy": "🟢 Easy",
                "moderate": "🟡 Moderate", 
                "advanced": "🟠 Advanced",
                "expert": "🔴 Expert"
            }
            st.write(difficulty_emoji.get(provider.difficulty.value, "❓"))
        
        with col4:
            setup_time = provider.avg_setup_time_minutes
            st.write(f"⏱️ ~{setup_time} min setup")
        
        # Status badges
        st.markdown("---")
        
        # Show recommendation level
        if trust_score >= 85:
            st.success(f"🌟 {rec_level}")
        elif trust_score >= 70:
            st.info(f"{rec_level}")
        elif trust_score >= 50:
            st.warning(f"{rec_level}")
        else:
            st.error(f"{rec_level}")
        
        # Key features
        col1, col2 = st.columns(2)
        
        with col1:
            if provider.has_free_tier:
                st.success("✅ Free tier available")
            else:
                st.error("❌ No free tier (paid only)")
            
            if provider.requires_approval:
                st.warning("⏳ Requires manual approval")
            else:
                st.success("⚡ Instant access")
        
        with col2:
            if provider.api_stable:
                st.success("✅ Stable API")
            else:
                st.warning("⚠️ API instability reported")
            
            if provider.pricing_changed:
                st.warning("⚠️ Recent pricing changes")
        
        # Caution flags (if any)
        if provider.caution_flags:
            st.markdown("**⚠️ Cautions:**")
            for flag in provider.caution_flags:
                st.warning(flag)
        
        # Recommended for
        if provider.recommended_for:
            st.markdown("**👥 Recommended for:**")
            st.write(", ".join(provider.recommended_for))
        
        # Expanded details
        if expanded:
            with st.expander("📋 Common Issues & Pro Tips", expanded=False):
                if provider.common_issues:
                    st.markdown("**Common Issues:**")
                    for issue in provider.common_issues:
                        st.write(f"• {issue}")
                
                if provider.pro_tips:
                    st.markdown("**💡 Pro Tips:**")
                    for tip in provider.pro_tips:
                        st.write(f"• {tip}")
            
            # Action buttons
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"📝 Sign Up - {provider.provider_name}", key=f"signup_{provider.provider_id}"):
                    st.markdown(f"**Sign up here:** [{provider.signup_url}]({provider.signup_url})")
                    st.info("After signing up, return here to enter your API key!")
            
            with col2:
                if st.button(f"🔑 Get API Key", key=f"key_{provider.provider_id}"):
                    st.markdown(f"**Get your API key:** [{provider.api_key_url}]({provider.api_key_url})")
            
            with col3:
                if st.button(f"📚 Documentation", key=f"docs_{provider.provider_id}"):
                    st.markdown(f"**View docs:** [{provider.documentation_url}]({provider.documentation_url})")


def streamlit_byok_onboarding():
    """
    Complete BYOK onboarding flow for Streamlit
    
    Returns:
        Tuple of (provider_id, api_key, provider_name) or (None, None, None)
    """
    
    st.markdown("# 🚀 BYOK Provider Onboarding")
    st.markdown("**Bring Your Own Key** - Choose your AI provider and get started!")
    
    registry = get_registry()
    
    # Show filter options
    st.markdown("---")
    st.markdown("## 🔍 Filter Providers")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        show_free_only = st.checkbox("Free tier only", value=True)
    
    with col2:
        max_difficulty = st.selectbox(
            "Max difficulty",
            options=["Easy", "Moderate", "Advanced", "Expert"],
            index=1
        )
        difficulty_map = {
            "Easy": ProviderDifficulty.EASY,
            "Moderate": ProviderDifficulty.MODERATE,
            "Advanced": ProviderDifficulty.ADVANCED,
            "Expert": ProviderDifficulty.EXPERT
        }
        max_diff = difficulty_map[max_difficulty]
    
    with col3:
        min_trust = st.slider("Min trust score", 0, 100, 70)
    
    # Get filtered providers
    providers = registry.get_recommended_providers(
        free_only=show_free_only,
        min_trust_score=min_trust,
        difficulty_max=max_diff
    )
    
    # Show statistics
    st.markdown("---")
    st.markdown("## 📊 Community Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_providers = len(registry.providers)
    total_users = sum(p.active_users for p in registry.providers.values())
    avg_success = sum(p.success_rate for p in registry.providers.values()) / max(total_providers, 1)
    recommended_count = len([p for p in registry.providers.values() if p.status == ProviderStatus.RECOMMENDED])
    
    with col1:
        st.metric("Total Providers", total_providers)
    
    with col2:
        st.metric("Active Users", f"{total_users:,}")
    
    with col3:
        st.metric("Avg Success Rate", f"{avg_success:.1f}%")
    
    with col4:
        st.metric("Recommended", recommended_count)
    
    # Show providers
    st.markdown("---")
    st.markdown(f"## ⭐ Recommended Providers ({len(providers)} found)")
    
    if not providers:
        st.warning("No providers match your filters. Try relaxing the criteria.")
        return None, None, None
    
    # Display each provider
    for i, provider in enumerate(providers):
        st.markdown(f"### {i+1}. {provider.provider_name}")
        render_provider_card(provider, expanded=True)
        
        # Key entry section
        with st.expander(f"🔑 Enter API Key for {provider.provider_name}", expanded=False):
            st.info(f"Already have an account? Enter your API key below. Need one? Click 'Sign Up' above!")
            
            api_key = st.text_input(
                f"API Key for {provider.provider_name}",
                type="password",
                key=f"api_key_input_{provider.provider_id}",
                help=f"Get your key from: {provider.api_key_url}"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button(f"✅ Use {provider.provider_name}", key=f"use_{provider.provider_id}"):
                    if api_key:
                        st.success(f"✅ Using {provider.provider_name}!")
                        st.session_state[f'selected_provider'] = provider.provider_id
                        st.session_state[f'selected_api_key'] = api_key
                        st.session_state[f'selected_provider_name'] = provider.provider_name
                        
                        # Record successful signup
                        registry.record_user_signup(provider.provider_id, success=True)
                        
                        return provider.provider_id, api_key, provider.provider_name
                    else:
                        st.error("Please enter an API key first!")
            
            with col2:
                if st.button(f"⭐ Rate Setup Experience", key=f"rate_{provider.provider_id}"):
                    st.session_state[f'show_rating_{provider.provider_id}'] = True
            
            # Show rating form if requested
            if st.session_state.get(f'show_rating_{provider.provider_id}', False):
                st.markdown("---")
                st.markdown("**How was your setup experience?**")
                
                rating = st.slider(
                    "Rating (1-5 stars)",
                    1, 5, 4,
                    key=f"rating_slider_{provider.provider_id}"
                )
                
                setup_time = st.number_input(
                    "Setup time (minutes)",
                    1, 120, provider.avg_setup_time_minutes,
                    key=f"setup_time_{provider.provider_id}"
                )
                
                feedback = st.text_area(
                    "Feedback (optional)",
                    key=f"feedback_{provider.provider_id}",
                    placeholder="Any issues or tips to share?"
                )
                
                if st.button("Submit Rating", key=f"submit_rating_{provider.provider_id}"):
                    registry.add_feedback(
                        provider.provider_id,
                        rating,
                        comment=feedback if feedback else None
                    )
                    registry.record_user_signup(
                        provider.provider_id,
                        success=True,
                        setup_time_minutes=setup_time
                    )
                    st.success("Thank you for your feedback! 🙏")
                    st.session_state[f'show_rating_{provider.provider_id}'] = False
                    st.rerun()
        
        st.markdown("---")
    
    # Show providers to avoid
    avoid_providers = [
        p for p in registry.list_all_providers()
        if p.status == ProviderStatus.AVOID or p.get_trust_score() < 30
    ]
    
    if avoid_providers:
        with st.expander("⚠️ Providers to Avoid", expanded=False):
            st.warning("These providers have low trust scores or are not recommended:")
            for provider in avoid_providers:
                st.markdown(f"**❌ {provider.provider_name}**")
                st.write(f"Trust Score: {provider.get_trust_score()}/100")
                if provider.caution_flags:
                    for flag in provider.caution_flags:
                        st.write(f"• {flag}")
                st.markdown("---")
    
    return None, None, None


def streamlit_provider_stats_widget():
    """Display provider statistics widget"""
    
    registry = get_registry()
    
    st.markdown("### 📊 Provider Statistics")
    
    # Get top 3 providers
    top_providers = registry.get_recommended_providers(
        free_only=True,
        min_trust_score=0
    )[:3]
    
    for provider in top_providers:
        trust = provider.get_trust_score()
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**{provider.provider_name}**")
        
        with col2:
            st.write(f"{trust:.0f}/100")
        
        with col3:
            stars = "⭐" * int(provider.star_rating)
            st.write(stars)


if __name__ == "__main__":
    # Demo the onboarding UI
    st.set_page_config(
        page_title="BYOK Provider Onboarding",
        page_icon="🚀",
        layout="wide"
    )
    
    provider_id, api_key, provider_name = streamlit_byok_onboarding()
    
    if provider_id:
        st.success(f"✅ Successfully configured {provider_name}!")
        st.balloons()
