#!/usr/bin/env python3
"""
Quick Integration Example

Shows how to integrate all PhD-level enhancements into Spiral Codex HUD
"""

import streamlit as st
from typing import Optional

# Import the new PhD-level components
from huggingface_diagnostic import HuggingFaceDiagnostic
from model_ui_sync import get_sync_enforcer, streamlit_model_selector
from provider_token_refresh import get_refresh_manager, streamlit_token_updater


def enhanced_provider_configuration():
    """
    Enhanced provider configuration with:
    - Auto-refreshing token management
    - Model-UI sync enforcement
    - HuggingFace diagnostics
    """
    
    st.header("☁️ Cloud Provider Configuration")
    
    # Get managers
    refresh_manager = get_refresh_manager()
    sync_enforcer = get_sync_enforcer()
    
    # === OpenRouter Configuration ===
    with st.expander("🌐 OpenRouter", expanded=True):
        st.markdown("**Status:** " + (
            "✅ Active" if st.session_state.get('openrouter_key') else "⚠️ No API key"
        ))
        
        # Token updater with auto-refresh
        col1, col2 = st.columns([3, 1])
        
        with col1:
            openrouter_key = st.text_input(
                "OpenRouter API Key",
                value=st.session_state.get('openrouter_key', ''),
                type="password",
                key="openrouter_token_input",
                help="Your OpenRouter API key (sk-or-v1-...)"
            )
        
        with col2:
            if st.button("💾 Save", key="save_openrouter"):
                if openrouter_key:
                    # Detect and handle token change
                    if refresh_manager.detect_token_change("OpenRouter", openrouter_key):
                        with st.spinner("🔄 Refreshing system..."):
                            success = refresh_manager.update_provider_token(
                                "OpenRouter",
                                openrouter_key,
                                auto_activate=True
                            )
                            
                            if success:
                                st.session_state.openrouter_key = openrouter_key
                                st.success("✅ Updated!")
                                st.rerun()
                            else:
                                st.error("❌ Update failed")
                    else:
                        st.session_state.openrouter_key = openrouter_key
                        st.info("Token unchanged")
        
        # Model selector with sync enforcement
        if st.session_state.get('openrouter_key'):
            st.markdown("**Select Model:**")
            
            selected_model = streamlit_model_selector(
                provider_name="OpenRouter",
                api_token=st.session_state.openrouter_key,
                key="openrouter_model_select",
                label="Available Models (validated)"
            )
            
            if selected_model:
                st.session_state.openrouter_model = selected_model
                st.success(f"Selected: {selected_model}")
            
            # Show catalog status
            catalog_status = sync_enforcer.get_catalog_status("OpenRouter")
            if catalog_status:
                st.caption(
                    f"📊 {catalog_status['model_count']} models available | "
                    f"Last sync: {catalog_status['last_sync'][:19]}"
                )
    
    # === HuggingFace Configuration ===
    with st.expander("🤗 Hugging Face", expanded=True):
        st.markdown("**Status:** " + (
            "✅ Active" if st.session_state.get('huggingface_key') else "⚠️ No API key"
        ))
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            hf_key = st.text_input(
                "HuggingFace Token",
                value=st.session_state.get('huggingface_key', ''),
                type="password",
                key="hf_token_input",
                help="Your HuggingFace token (hf_...)"
            )
        
        with col2:
            if st.button("💾 Save", key="save_hf"):
                if hf_key:
                    if refresh_manager.detect_token_change("Hugging Face", hf_key):
                        with st.spinner("🔄 Refreshing system..."):
                            success = refresh_manager.update_provider_token(
                                "Hugging Face",
                                hf_key,
                                auto_activate=True
                            )
                            
                            if success:
                                st.session_state.huggingface_key = hf_key
                                st.success("✅ Updated!")
                                st.rerun()
                            else:
                                st.error("❌ Update failed")
                    else:
                        st.session_state.huggingface_key = hf_key
                        st.info("Token unchanged")
        
        # HuggingFace Diagnostic Tool
        if st.session_state.get('huggingface_key'):
            st.markdown("---")
            st.markdown("**🔬 Diagnostic Tools**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🧪 Run Full Diagnostic", key="hf_diag_full"):
                    with st.spinner("Running comprehensive diagnostic..."):
                        diagnostic = HuggingFaceDiagnostic(st.session_state.huggingface_key)
                        result = diagnostic.run_full_diagnostic()
                        
                        # Show results
                        if result.success:
                            st.success(f"✅ All tests passed! {len(result.available_models)} models available")
                        else:
                            st.error(f"❌ Diagnostic failed: {result.error_message}")
                            
                            # Show fix steps
                            with st.expander("📋 Fix Steps", expanded=True):
                                for step in result.fix_steps:
                                    st.markdown(step)
                            
                            # Show curl commands
                            if result.curl_commands:
                                with st.expander("💻 Manual Test Commands"):
                                    st.code('\n'.join(result.curl_commands), language='bash')
            
            with col2:
                if st.button("📝 Generate Curl Tests", key="hf_curl"):
                    diagnostic = HuggingFaceDiagnostic(st.session_state.huggingface_key)
                    commands = diagnostic._generate_curl_commands()
                    
                    st.code('\n'.join(commands), language='bash')
                    st.info("Copy these commands and run them in your terminal")
            
            with col3:
                if st.button("🔄 Force Resync", key="hf_resync"):
                    with st.spinner("Resyncing models..."):
                        sync_enforcer.clear_cache("Hugging Face")
                        catalog = sync_enforcer.sync_provider_models(
                            "Hugging Face",
                            st.session_state.huggingface_key,
                            force_refresh=True
                        )
                        
                        if catalog.validation_passed:
                            st.success(f"✅ Synced {len(catalog.models)} models")
                        else:
                            st.error(f"❌ Sync failed: {catalog.error_message}")


def enhanced_inference_interface():
    """
    Enhanced inference interface with pre-send validation
    """
    
    st.header("💬 Inference Interface")
    
    # Provider selection
    providers = []
    if st.session_state.get('openrouter_key'):
        providers.append("OpenRouter")
    if st.session_state.get('huggingface_key'):
        providers.append("Hugging Face")
    
    if not providers:
        st.warning("⚠️ Configure at least one provider above")
        return
    
    selected_provider = st.selectbox("Select Provider", providers)
    
    # Get validated models for selected provider
    sync_enforcer = get_sync_enforcer()
    
    if selected_provider == "OpenRouter":
        api_key = st.session_state.openrouter_key
    else:
        api_key = st.session_state.huggingface_key
    
    # Use enforced model selector
    selected_model = streamlit_model_selector(
        provider_name=selected_provider,
        api_token=api_key,
        key="inference_model_select",
        label="Select Model (validated only)"
    )
    
    if not selected_model:
        st.info("👆 Select a validated model to continue")
        return
    
    # Prompt input
    prompt = st.text_area(
        "Enter your prompt",
        height=150,
        placeholder="Type your message here..."
    )
    
    # Pre-send validation
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("🚀 Send Request", type="primary", width="stretch"):
            if not prompt:
                st.error("Please enter a prompt")
            else:
                # Final validation before send
                valid, error = sync_enforcer.validate_model_selection(
                    selected_provider,
                    selected_model,
                    api_key
                )
                
                if not valid:
                    st.error(f"❌ Validation failed: {error}")
                    
                    # Show alternatives
                    alt_models = sync_enforcer.get_ui_models(selected_provider, api_key)
                    if alt_models:
                        st.info(f"✅ Try one of these: {', '.join(alt_models[:5])}")
                else:
                    # ✅ ZERO DOOMED REQUESTS - This request is guaranteed valid
                    st.success("✅ Request validated - sending to provider...")
                    
                    # Your actual inference code here
                    with st.spinner("Processing..."):
                        st.info("(Integrate with your existing inference system)")
    
    with col2:
        if st.button("🧹 Clear", width="stretch"):
            st.rerun()


def enhanced_system_status():
    """
    Enhanced system status dashboard
    """
    
    st.header("📊 System Status")
    
    refresh_manager = get_refresh_manager()
    sync_enforcer = get_sync_enforcer()
    
    # Get status
    refresh_status = refresh_manager.get_refresh_status()
    
    # Display provider status
    cols = st.columns(len(refresh_status) if refresh_status else 1)
    
    for idx, (provider_name, status) in enumerate(refresh_status.items()):
        with cols[idx]:
            st.markdown(f"**{provider_name}**")
            
            # Status indicators
            if status['has_token'] and status['is_active']:
                st.success("✅ Active")
            elif status['has_token']:
                st.warning("⚠️ Inactive")
            else:
                st.error("❌ No token")
            
            # Catalog info
            catalog_status = sync_enforcer.get_catalog_status(provider_name)
            if catalog_status:
                st.metric(
                    "Models",
                    catalog_status['model_count'],
                    delta="validated" if catalog_status['validation_passed'] else "failed"
                )
                
                st.caption(f"Last sync: {catalog_status['last_sync'][:19]}")
            
            # Last updated
            if status['last_updated'] != 'unknown':
                st.caption(f"Updated: {status['last_updated'][:19]}")


def main():
    """Main application"""
    
    st.set_page_config(
        page_title="Enhanced Spiral Codex HUD",
        page_icon="🌀",
        layout="wide"
    )
    
    st.title("🌀 Spiral Codex HUD - PhD Level")
    st.markdown("**Zero Doomed Requests** | **100% Validated Models** | **Intelligent Refresh**")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        if st.button("🔄 Refresh All", width="stretch"):
            sync_enforcer = get_sync_enforcer()
            sync_enforcer.clear_cache()
            st.rerun()
        
        if st.button("📊 Export Diagnostics", width="stretch"):
            sync_enforcer = get_sync_enforcer()
            sync_enforcer.export_diagnostics("diagnostics_export.json")
            st.success("Exported to diagnostics_export.json")
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["🔧 Configuration", "💬 Inference", "📊 Status"])
    
    with tab1:
        enhanced_provider_configuration()
    
    with tab2:
        enhanced_inference_interface()
    
    with tab3:
        enhanced_system_status()


if __name__ == "__main__":
    main()
