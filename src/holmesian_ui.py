#!/usr/bin/env python3
"""
Holmesian UI Components for Streamlit

Zero dead-end user interfaces powered by Sherlock Holmes logic.
Always shows only viable solutions, with clear guidance when none exist.
"""

import streamlit as st
from typing import List, Dict, Optional, Any
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from holmesian_solver import (
    HolmesianSolver,
    Solution,
    SolutionViability,
    holmesian_autocorrect
)


def streamlit_holmesian_selector(
    possibilities: List[Dict[str, Any]],
    selector_label: str = "Select an option",
    free_mode: bool = True,
    show_impossible: bool = False,
    key_prefix: str = "holmesian"
) -> Optional[str]:
    """
    Holmesian smart selector for Streamlit
    
    Args:
        possibilities: List of possible options
        selector_label: Label for selector
        free_mode: Only show free options
        show_impossible: Show impossible options (grayed out)
        key_prefix: Unique key prefix for Streamlit widgets
        
    Returns:
        Selected option ID or None
    """
    
    # Solve for viable options
    solutions, recommendation = holmesian_autocorrect(
        possibilities,
        free_mode=free_mode
    )
    
    # Show recommendation banner
    action = recommendation['action']
    message = recommendation['message']
    
    if action == 'auto_select':
        # Auto-selected single option
        auto_select = recommendation['auto_select']
        st.success(f"✅ {message}")
        st.info(f"Using: **{auto_select.name}**")
        
        for suggestion in recommendation['suggestions']:
            st.caption(suggestion)
        
        return auto_select.id
    
    elif action == 'choose_from_optimal':
        # Multiple optimal choices
        st.success(f"🏆 {message}")
        
    elif action == 'choose_with_compromises':
        # Degraded options only
        st.warning(f"⚠️ {message}")
        for suggestion in recommendation['suggestions']:
            st.caption(suggestion)
    
    elif action == 'guide_resolution':
        # No viable options - show resolution steps
        st.error(f"❌ {message}")
        
        with st.expander("📋 How to Fix This", expanded=True):
            for suggestion in recommendation['suggestions']:
                if suggestion.startswith("Steps to resolve"):
                    st.markdown("**Steps to resolve:**")
                elif suggestion.strip().startswith(tuple(f"{i}." for i in range(10))):
                    st.markdown(f"  {suggestion}")
                else:
                    st.write(suggestion)
        
        return None
    
    elif action == 'suggest_mode_change':
        # Need mode change
        st.error(f"❌ {message}")
        
        with st.expander("💡 Suggested Actions", expanded=True):
            for suggestion in recommendation['suggestions']:
                if suggestion.startswith("Options:"):
                    st.markdown("**Your options:**")
                elif suggestion.strip().startswith("•"):
                    st.markdown(suggestion)
                else:
                    st.write(suggestion)
        
        return None
    
    else:
        # Error case
        st.error(f"❌ {message}")
        return None
    
    # Show selector for viable options
    if not solutions:
        return None
    
    # Create selector options
    option_labels = []
    option_ids = []
    
    for solution in solutions:
        option_labels.append(solution.get_display_name())
        option_ids.append(solution.id)
    
    # Add impossible options if requested
    if show_impossible and hasattr(streamlit_holmesian_selector, '_last_solver'):
        solver = streamlit_holmesian_selector._last_solver
        for imp in solver.impossibilities:
            # Extract name from message
            name = imp.message.split(':')[0] if ':' in imp.message else "Option"
            option_labels.append(f"❌ {name} (unavailable)")
            option_ids.append(None)
    
    # Show selector
    selected_label = st.selectbox(
        selector_label,
        options=option_labels,
        key=f"{key_prefix}_selector"
    )
    
    # Get selected ID
    selected_idx = option_labels.index(selected_label)
    selected_id = option_ids[selected_idx]
    
    if selected_id is None:
        st.error("This option is not currently available")
        return None
    
    # Show selected solution details
    selected_solution = solutions[selected_idx]
    
    with st.expander("ℹ️ Option Details", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Viability Score", f"{selected_solution.score:.1f}/100")
            
            if selected_solution.is_free:
                st.success("✅ Free tier")
            else:
                st.warning("💰 Paid option")
        
        with col2:
            if selected_solution.is_healthy:
                st.success("✅ Healthy")
            else:
                st.error("❌ Unhealthy")
            
            if selected_solution.is_authenticated:
                st.success("✅ Authenticated")
            else:
                st.error("❌ Not authenticated")
        
        if selected_solution.reasons:
            st.markdown("**Why this works:**")
            for reason in selected_solution.reasons:
                st.write(f"• {reason}")
        
        if selected_solution.warnings:
            st.markdown("**⚠️ Warnings:**")
            for warning in selected_solution.warnings:
                st.warning(warning)
        
        if selected_solution.compromises:
            st.markdown("**ℹ️ Compromises:**")
            for compromise in selected_solution.compromises:
                st.info(compromise)
    
    return selected_id


def streamlit_holmesian_diagnostic(
    possibilities: List[Dict[str, Any]],
    free_mode: bool = True
):
    """
    Show diagnostic view of Holmesian evaluation
    
    Useful for debugging and understanding why certain options are impossible
    """
    
    st.markdown("### 🔍 Holmesian Diagnostic View")
    st.caption("Understanding why each option is or isn't viable")
    
    solver = HolmesianSolver(free_mode=free_mode)
    solutions, impossibilities = solver.solve(possibilities)
    
    # Show statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Options", len(possibilities))
    
    with col2:
        viable_count = len([s for s in solutions if s.viability != SolutionViability.IMPOSSIBLE])
        st.metric("Viable", viable_count)
    
    with col3:
        optimal_count = len([s for s in solutions if s.viability == SolutionViability.OPTIMAL])
        st.metric("Optimal", optimal_count)
    
    with col4:
        st.metric("Impossible", len(impossibilities))
    
    # Show viable solutions
    if solutions:
        st.markdown("#### ✅ Viable Solutions")
        
        for solution in solutions:
            with st.expander(f"{solution.get_display_name()} - Score: {solution.score:.1f}/100"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Status:**")
                    st.write(f"• Free: {'✅' if solution.is_free else '❌'}")
                    st.write(f"• Available: {'✅' if solution.is_available else '❌'}")
                    st.write(f"• Healthy: {'✅' if solution.is_healthy else '❌'}")
                    st.write(f"• Authenticated: {'✅' if solution.is_authenticated else '❌'}")
                
                with col2:
                    st.write("**Viability:**")
                    st.write(f"Level: {solution.viability.value}")
                    st.write(f"Score: {solution.score:.1f}/100")
                
                if solution.reasons:
                    st.markdown("**✓ Reasons this works:**")
                    for reason in solution.reasons:
                        st.success(reason)
                
                if solution.warnings:
                    st.markdown("**⚠️ Warnings:**")
                    for warning in solution.warnings:
                        st.warning(warning)
                
                if solution.limitations:
                    st.markdown("**⚠️ Limitations:**")
                    for limitation in solution.limitations:
                        st.info(limitation)
    
    # Show impossibilities
    if impossibilities:
        st.markdown("#### ❌ Impossible Options")
        
        for imp in impossibilities:
            with st.expander(f"❌ {imp.message}"):
                st.error(f"**Reason:** {imp.reason.value}")
                
                if imp.suggestion:
                    st.info(f"**💡 Suggestion:** {imp.suggestion}")
                
                if imp.can_be_resolved:
                    st.success("✅ This can be resolved!")
                    
                    if imp.resolution_steps:
                        st.markdown("**Steps to resolve:**")
                        for i, step in enumerate(imp.resolution_steps, 1):
                            st.write(f"{i}. {step}")
                else:
                    st.warning("⚠️ This cannot be resolved automatically")


def streamlit_smart_provider_selector(
    providers: List[Dict[str, Any]],
    free_mode: bool = True
) -> Optional[str]:
    """
    Smart provider selector with Holmesian logic
    
    Args:
        providers: List of provider dicts
        free_mode: Only show free providers
        
    Returns:
        Selected provider ID or None
    """
    
    st.markdown("### 🚀 Select AI Provider")
    st.caption("Only showing options that will actually work")
    
    return streamlit_holmesian_selector(
        possibilities=providers,
        selector_label="Choose Provider",
        free_mode=free_mode,
        show_impossible=True,
        key_prefix="provider"
    )


def streamlit_smart_model_selector(
    models: List[Dict[str, Any]],
    free_mode: bool = True
) -> Optional[str]:
    """
    Smart model selector with Holmesian logic
    
    Args:
        models: List of model dicts
        free_mode: Only show free models
        
    Returns:
        Selected model ID or None
    """
    
    st.markdown("### 🤖 Select AI Model")
    st.caption("Impossible options automatically filtered out")
    
    return streamlit_holmesian_selector(
        possibilities=models,
        selector_label="Choose Model",
        free_mode=free_mode,
        show_impossible=False,
        key_prefix="model"
    )


if __name__ == "__main__":
    # Demo the Holmesian UI
    st.set_page_config(
        page_title="Holmesian Autocorrection Demo",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Holmesian Autocorrection Layer")
    st.markdown("*When you have eliminated the impossible, whatever remains must be the truth.*")
    st.markdown("— Sherlock Holmes")
    
    st.markdown("---")
    
    # Demo data
    demo_providers = [
        {
            'id': 'openrouter',
            'name': 'OpenRouter',
            'available': True,
            'healthy': True,
            'authenticated': True,
            'is_free': True,
            'requires_payment': False,
            'trust_score': 95.5
        },
        {
            'id': 'deepseek',
            'name': 'DeepSeek',
            'available': True,
            'healthy': True,
            'authenticated': False,
            'is_free': True,
            'requires_payment': False,
            'trust_score': 89.0
        },
        {
            'id': 'claude',
            'name': 'Anthropic Claude',
            'available': True,
            'healthy': True,
            'authenticated': True,
            'is_free': False,
            'requires_payment': True,
            'trust_score': 95.2
        },
        {
            'id': 'broken',
            'name': 'Broken Provider',
            'available': True,
            'healthy': False,
            'authenticated': True,
            'is_free': True,
            'requires_payment': False,
            'trust_score': 30.0
        }
    ]
    
    # Show selector
    selected = streamlit_smart_provider_selector(demo_providers, free_mode=True)
    
    if selected:
        st.success(f"✅ Selected: {selected}")
    
    st.markdown("---")
    
    # Show diagnostic view
    streamlit_holmesian_diagnostic(demo_providers, free_mode=True)
