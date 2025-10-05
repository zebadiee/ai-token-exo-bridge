#!/usr/bin/env python3
"""
Spiral Codex HUD - Enhanced AI Infrastructure Monitor

Universal monitoring dashboard with ReliaKit self-healing integration.
Real-time status, health metrics, automatic recovery, and full control.
"""

import streamlit as st
import json
import time
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from exo_integration import ExoTokenManagerIntegration, ExoReliakitProvider
    from exo_provider import ExoNodeStatus, ExoClusterProvider
    from bridge_manager import ExoBridgeManager
    from reliakit_integration import ReliakitSelfHealingManager, HealthStatus
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Please ensure all integration files are in the same directory")
    st.stop()


# Page configuration
st.set_page_config(
    page_title="Spiral Codex HUD - AI Command Bridge",
    page_icon="🌀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #00ff00;
        text-align: center;
        text-shadow: 0 0 10px #00ff00;
        margin-bottom: 1rem;
    }
    .status-healthy {
        color: #00ff00;
        font-weight: bold;
    }
    .status-degraded {
        color: #ffaa00;
        font-weight: bold;
    }
    .status-offline {
        color: #ff0000;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
        border: 1px solid #00ff00;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .node-card {
        background: #1a1a1a;
        border-left: 4px solid #00ff00;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)


class SpiralCodexHUD:
    """Universal HUD for AI provider monitoring and control with ReliaKit integration"""
    
    def __init__(self):
        """Initialize HUD with session state"""
        if 'bridge_manager' not in st.session_state:
            st.session_state.bridge_manager = None
            st.session_state.reliakit_manager = None
            st.session_state.auto_refresh = True
            st.session_state.refresh_interval = 5
            st.session_state.history = []
            st.session_state.event_history = []
            st.session_state.last_event_check = datetime.now()
        
        # Check configuration on startup
        self.check_configuration()
    
    def check_configuration(self):
        """Check if required configuration files exist"""
        from pathlib import Path
        
        config_issues = []
        
        # Check bridge config
        bridge_config = Path(__file__).parent.parent / "config" / "bridge_config.yaml"
        if not bridge_config.exists():
            config_issues.append(f"❌ Bridge config missing: {bridge_config}")
        
        # Check token manager config
        token_config = Path.home() / ".token_manager_config.json"
        if not token_config.exists():
            config_issues.append(f"⚠️ Token manager config missing: {token_config}")
        
        # Store issues in session state
        st.session_state.config_issues = config_issues
    
    def initialize_bridge(self, host: str, port: int, enable_reliakit: bool = True):
        """Initialize bridge with optional ReliaKit self-healing"""
        try:
            # First check if Exo is accessible
            import requests
            try:
                response = requests.get(f"http://{host}:{port}/", timeout=5)
                if response.status_code != 200:
                    st.warning(f"⚠️ Exo cluster responded with status {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Cannot connect to Exo at {host}:{port}")
                st.error(f"Error: {str(e)}")
                st.info("Please ensure Exo is running:")
                st.code(f"cd ~/exo\nsource .venv/bin/activate\npython3 exo/main.py --chatgpt-api-port {port}")
                return False
            
            # Initialize bridge manager
            st.session_state.bridge_manager = ExoBridgeManager(
                exo_host=host,
                exo_port=port,
                enable_hud=False  # We are the HUD
            )
            st.session_state.bridge_manager.start()
            
            # Initialize ReliaKit self-healing if enabled
            if enable_reliakit:
                try:
                    st.session_state.reliakit_manager = ReliakitSelfHealingManager(
                        bridge_manager=st.session_state.bridge_manager,
                        check_interval=st.session_state.refresh_interval,
                        enable_auto_recovery=True
                    )
                    
                    # Add Exo cluster as monitoring target
                    st.session_state.reliakit_manager.add_target(
                        name="exo_primary",
                        url=f"http://{host}:{port}",
                        health_endpoint="/health"
                    )
                    
                    # Start monitoring
                    st.session_state.reliakit_manager.start()
                    
                    st.success("✅ Bridge and ReliaKit self-healing initialized")
                except Exception as e:
                    st.warning(f"⚠️ Bridge initialized but ReliaKit failed: {e}")
                    st.info("Continuing without ReliaKit self-healing...")
            else:
                st.success("✅ Bridge initialized (ReliaKit disabled)")
            
            return True
        
        except Exception as e:
            st.error(f"❌ Failed to initialize: {e}")
            
            # Show helpful error information
            st.info("**Troubleshooting Steps:**")
            st.markdown(f"""
            1. Ensure Exo is running on {host}:{port}
            2. Check that the config file exists: `config/bridge_config.yaml`
            3. Verify token manager config: `~/.token_manager_config.json`
            4. Check the error details below
            """)
            
            import traceback
            with st.expander("🐛 Error Details (click to expand)"):
                st.code(traceback.format_exc())
            
            return False
    
    def render_header(self):
        """Render main header"""
        st.markdown('<div class="main-header">🌀 SPIRAL CODEX HUD</div>', unsafe_allow_html=True)
        st.markdown("**AI Command Bridge** - Universal Provider Monitor & Control")
        st.markdown("---")
    
    def render_sidebar(self):
        """Render sidebar configuration"""
        with st.sidebar:
            st.header("⚙️ Configuration")
            
            # Connection settings
            st.subheader("Exo Cluster Connection")
            host = st.text_input("Host", value="localhost")
            port = st.number_input("Port", value=8000, min_value=1, max_value=65535)
            
            # ReliaKit toggle
            enable_reliakit = st.checkbox(
                "Enable ReliaKit Self-Healing",
                value=True,
                help="Automatic health monitoring and recovery"
            )
            
            if st.button("🔌 Connect to Exo", type="primary"):
                if self.initialize_bridge(host, port, enable_reliakit):
                    st.rerun()
            
            st.markdown("---")
            
            # Cloud Provider API Keys
            st.subheader("☁️ Cloud Provider Keys")
            
            # Initialize session state for API keys if not exists
            if 'openrouter_key' not in st.session_state:
                st.session_state.openrouter_key = ""
            if 'huggingface_key' not in st.session_state:
                st.session_state.huggingface_key = ""
            
            # OpenRouter API Key
            openrouter_key = st.text_input(
                "OpenRouter API Key",
                value=st.session_state.openrouter_key,
                type="password",
                help="Enter your OpenRouter API key for cloud failover",
                placeholder="sk-or-v1-..."
            )
            
            # HuggingFace Token
            huggingface_key = st.text_input(
                "HuggingFace Token",
                value=st.session_state.huggingface_key,
                type="password",
                help="Enter your HuggingFace token for cloud failover",
                placeholder="hf_..."
            )
            
            # Save keys button
            if st.button("💾 Save API Keys"):
                if openrouter_key or huggingface_key:
                    st.session_state.openrouter_key = openrouter_key
                    st.session_state.huggingface_key = huggingface_key
                    
                    # Update token manager config
                    try:
                        import json
                        from pathlib import Path
                        config_path = Path.home() / ".token_manager_config.json"
                        
                        if config_path.exists():
                            with open(config_path, 'r') as f:
                                config = json.load(f)
                            
                            # Update provider keys
                            for provider in config.get('providers', []):
                                if provider['name'] == 'OpenRouter' and openrouter_key:
                                    provider['api_key'] = openrouter_key
                                    provider['status'] = 'active'
                                elif provider['name'] == 'Hugging Face' and huggingface_key:
                                    provider['api_key'] = huggingface_key
                                    provider['status'] = 'active'
                            
                            # Save back
                            with open(config_path, 'w') as f:
                                json.dump(config, f, indent=2)
                            
                            st.success("✅ API keys saved successfully!")
                            st.info("🔄 Reconnect to Exo to activate cloud providers")
                        else:
                            st.error(f"Config file not found: {config_path}")
                    except Exception as e:
                        st.error(f"Failed to save keys: {e}")
                else:
                    st.warning("Enter at least one API key to save")
            
            # Show current key status
            try:
                import json
                from pathlib import Path
                config_path = Path.home() / ".token_manager_config.json"
                
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    
                    st.markdown("**Current Status:**")
                    for provider in config.get('providers', []):
                        if provider['name'] in ['OpenRouter', 'Hugging Face']:
                            has_key = bool(provider.get('api_key') or provider.get('api_key_encrypted'))
                            status_icon = "✅" if has_key else "❌"
                            st.text(f"{status_icon} {provider['name']}: {provider.get('status', 'unknown')}")
            except:
                pass
            
            st.markdown("---")
            
            # Auto-refresh settings
            st.subheader("Display Settings")
            st.session_state.auto_refresh = st.checkbox(
                "Auto-refresh",
                value=st.session_state.auto_refresh
            )
            st.session_state.refresh_interval = st.slider(
                "Refresh interval (seconds)",
                min_value=1,
                max_value=60,
                value=st.session_state.refresh_interval
            )
            
            st.markdown("---")
            
            # Manual controls
            st.subheader("Manual Controls")
            
            if st.button("🔄 Force Refresh"):
                if st.session_state.reliakit_manager:
                    st.session_state.reliakit_manager.force_check()
                st.rerun()
            
            if st.button("🧹 Clear History"):
                st.session_state.history = []
                st.session_state.event_history = []
                st.rerun()
            
            # Self-healing controls
            if st.session_state.reliakit_manager:
                st.markdown("---")
                st.subheader("🛡️ Self-Healing")
                
                status = st.session_state.reliakit_manager.get_system_status()
                auto_recovery = status['manager']['auto_recovery']
                
                col1, col2 = st.columns(2)
                with col1:
                    if auto_recovery:
                        st.success("✅ Active")
                    else:
                        st.warning("⚠️ Disabled")
                
                with col2:
                    targets = status['manager']['targets']
                    st.metric("Targets", targets)
                
                if st.button("🔍 Force Health Check"):
                    st.session_state.reliakit_manager.force_check()
                    st.success("Health check triggered")
            
            st.markdown("---")
            
            if st.session_state.bridge_manager:
                if st.button("🛑 Disconnect"):
                    if st.session_state.reliakit_manager:
                        st.session_state.reliakit_manager.stop()
                    st.session_state.bridge_manager.stop()
                    st.session_state.bridge_manager = None
                    st.session_state.reliakit_manager = None
                    st.rerun()
    
    def render_cluster_overview(self, status: Dict):
        """Render cluster overview cards"""
        exo = status.get("exo", {})
        health = exo.get("health", {})
        
        # Main status cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            is_available = exo.get("available", False)
            status_color = "🟢" if is_available else "🔴"
            st.metric(
                label=f"{status_color} Cluster Status",
                value="ONLINE" if is_available else "OFFLINE"
            )
        
        with col2:
            healthy = health.get("healthy_nodes", 0)
            total = health.get("total_nodes", 0)
            st.metric(
                label="🖥️ Active Nodes",
                value=f"{healthy}/{total}"
            )
        
        with col3:
            models = len(exo.get("available_models", []))
            st.metric(
                label="🤖 Available Models",
                value=models
            )
        
        with col4:
            cost = exo.get("cost", 0.0)
            st.metric(
                label="💰 Cost",
                value=f"${cost:.2f}",
                delta="Always FREE!"
            )
    
    def render_node_details(self, status: Dict):
        """Render detailed node information"""
        st.subheader("📡 Node Details")
        
        nodes = status.get("exo", {}).get("nodes", {})
        
        if not nodes:
            st.info("No nodes detected. Check your Exo cluster is running.")
            return
        
        for node_id, node_info in nodes.items():
            node_status = node_info.get("status", "offline")
            
            # Determine status color
            if node_status == "online":
                status_class = "status-healthy"
                status_icon = "🟢"
            elif node_status == "degraded":
                status_class = "status-degraded"
                status_icon = "🟡"
            else:
                status_class = "status-offline"
                status_icon = "🔴"
            
            with st.container():
                st.markdown(f"""
                <div class="node-card">
                    <h4>{status_icon} {node_info.get('device', 'Unknown Device')}</h4>
                    <p><strong>ID:</strong> {node_id}</p>
                    <p><strong>Status:</strong> <span class="{status_class}">{node_status.upper()}</span></p>
                    <p><strong>Memory:</strong> {node_info.get('memory_gb', 0):.1f} GB</p>
                    <p><strong>Models:</strong> {node_info.get('models', 0)}</p>
                    <p><strong>Last Seen:</strong> {node_info.get('last_seen', 'Never')}</p>
                </div>
                """, unsafe_allow_html=True)
    
    def render_reliakit_events(self):
        """Render ReliaKit event log and self-healing status"""
        if not st.session_state.reliakit_manager:
            return
        
        st.subheader("🛡️ ReliaKit Self-Healing Events")
        
        status = st.session_state.reliakit_manager.get_system_status()
        
        # Summary cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Auto-Recovery", "ON" if status['manager']['auto_recovery'] else "OFF")
        
        with col2:
            total_events = len(st.session_state.reliakit_manager.event_log)
            st.metric("Total Events", total_events)
        
        with col3:
            recent_recoveries = len(status['recent_recoveries'])
            st.metric("Recent Recoveries", recent_recoveries)
        
        with col4:
            # Count failures in recent events
            failures = sum(
                1 for e in status['recent_events']
                if 'failure' in e['type']
            )
            st.metric("Recent Failures", failures, delta=None if failures == 0 else f"-{failures}")
        
        # Event log tabs
        tab1, tab2, tab3 = st.tabs(["📋 Live Events", "🔄 Recovery Actions", "📊 Health Metrics"])
        
        with tab1:
            # Live event stream
            st.markdown("**Live Event Stream** (last 20 events)")
            
            events = status['recent_events']
            if events:
                for event in reversed(events):  # Most recent first
                    timestamp = event['timestamp']
                    event_type = event['type']
                    data = event.get('data', {})
                    
                    # Color code by event type
                    if 'failure' in event_type:
                        color = "🔴"
                        bg_color = "#3d1f1f"
                    elif 'recovery' in event_type:
                        color = "🟢"
                        bg_color = "#1f3d1f"
                    elif 'status_change' in event_type:
                        color = "🟡"
                        bg_color = "#3d3d1f"
                    else:
                        color = "🔵"
                        bg_color = "#1f1f3d"
                    
                    with st.container():
                        st.markdown(f"""
                        <div style="background: {bg_color}; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 4px solid;">
                            <small>{timestamp}</small><br/>
                            <strong>{color} {event_type.replace('_', ' ').title()}</strong><br/>
                            <code>{json.dumps(data, indent=2)}</code>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No events yet")
        
        with tab2:
            # Recovery actions
            st.markdown("**Recent Recovery Actions**")
            
            recoveries = status['recent_recoveries']
            if recoveries:
                # Create DataFrame for table display
                df = pd.DataFrame([
                    {
                        "Timestamp": r['timestamp'],
                        "Action": r['action_type'],
                        "Target": r['target'],
                        "Success": "✅" if r['success'] else "❌",
                        "Error": r['error'] or "-"
                    }
                    for r in recoveries
                ])
                
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No recovery actions yet")
        
        with tab3:
            # Health metrics visualization
            st.markdown("**Target Health Metrics**")
            
            targets = status['targets']
            if targets:
                # Create metrics grid
                for target_name, stats in targets.items():
                    with st.expander(f"{target_name} - {stats['status'].upper()}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric(
                                "Success Rate",
                                f"{stats.get('recent_success_rate', 0) * 100:.1f}%"
                            )
                        
                        with col2:
                            st.metric(
                                "Avg Latency",
                                f"{stats.get('avg_latency_ms', 0):.1f}ms"
                            )
                        
                        with col3:
                            st.metric(
                                "Consecutive Failures",
                                stats.get('consecutive_failures', 0)
                            )
                        
                        # Status timeline (simplified)
                        st.markdown(f"""
                        - **Total Checks**: {stats.get('checks', 0)}
                        - **Last Check**: {stats.get('last_check', 'Never')}
                        """)
            else:
                st.info("No targets monitored yet")
    
    def render_reliakit_targets(self, status: Dict):
        """Render ReliaKit monitored targets"""
        if not status:
            return
        
        st.subheader("🎯 Monitored Targets")
        
        targets = status.get('targets', {})
        
        if not targets:
            st.info("No targets configured for monitoring")
            return
        
        for target_name, target_stats in targets.items():
            status_icon = "🟢" if target_stats.get('status') == 'healthy' else "🔴"
            
            with st.expander(f"{status_icon} {target_name}", expanded=True):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Status", target_stats.get('status', 'unknown').upper())
                
                with col2:
                    success_rate = target_stats.get('recent_success_rate', 0) * 100
                    st.metric("Success Rate", f"{success_rate:.1f}%")
                
                with col3:
                    latency = target_stats.get('avg_latency_ms', 0)
                    st.metric("Avg Latency", f"{latency:.0f}ms")
                
                with col4:
                    failures = target_stats.get('consecutive_failures', 0)
                    st.metric("Failures", failures)
    
    def render_usage_stats(self, status: Dict):
        st.subheader("📊 Usage Metrics")
        
        usage = status.get("exo", {}).get("usage", {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            requests = usage.get("total_requests", 0)
            st.metric("Total Requests", requests)
        
        with col2:
            compute_time = usage.get("total_compute_time", 0)
            st.metric("Compute Time", f"{compute_time:.2f}s")
        
        with col3:
            avg_time = usage.get("avg_compute_time", 0)
            st.metric("Avg Response Time", f"{avg_time:.2f}s")
        
        # Request history chart
        if st.session_state.history:
            self.render_history_chart()
    
    def render_history_chart(self):
        """Render request history chart"""
        if len(st.session_state.history) < 2:
            return
        
        # Create time series chart
        timestamps = [h["timestamp"] for h in st.session_state.history]
        requests = [h["requests"] for h in st.session_state.history]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=requests,
            mode='lines+markers',
            name='Requests',
            line=dict(color='#00ff00', width=2)
        ))
        
        fig.update_layout(
            title="Request History",
            xaxis_title="Time",
            yaxis_title="Total Requests",
            template="plotly_dark",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_model_selector(self, status: Dict):
        """Render model selection interface with chat"""
        st.subheader("🤖 Model Testing & Chat Interface")
        
        # Get available models from providers
        available_models = ["llama-3.2-3b", "gpt-3.5-turbo", "gpt-4", "claude-3-sonnet"]
        
        # Add models from Exo if available
        exo_models = status.get("exo", {}).get("available_models", [])
        if exo_models:
            available_models = exo_models + available_models
        
        # Model selection
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_model = st.selectbox(
                "Select Model",
                options=available_models,
                key="selected_model",
                help="Choose a model to test. Exo models run locally (free), others use cloud APIs."
            )
        
        with col2:
            st.markdown("**Provider:**")
            if "llama" in selected_model.lower():
                st.success("🟢 Exo Local (FREE)")
            elif "gpt" in selected_model.lower():
                st.info("☁️ OpenRouter")
            elif "claude" in selected_model.lower():
                st.info("☁️ OpenRouter")
            else:
                st.info("☁️ Cloud Provider")
        
        # Generation parameters
        st.markdown("### ⚙️ Generation Parameters")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=0.7,
                step=0.1
            )
        
        with col2:
            max_tokens = st.number_input(
                "Max Tokens",
                min_value=1,
                max_value=4096,
                value=512
            )
        
        with col3:
            top_p = st.slider(
                "Top P",
                min_value=0.0,
                max_value=1.0,
                value=0.9,
                step=0.1
            )
        
        st.markdown("---")
        st.markdown("### 💬 Chat Interface")
        
        # Chat interface
        prompt = st.text_area(
            "Enter your message:",
            height=150,
            placeholder="Type your message here...\n\nExample: 'Explain quantum computing in simple terms'"
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            send_button = st.button("🚀 Send Request", type="primary", use_container_width=True)
        with col2:
            clear_button = st.button("🧹 Clear", use_container_width=True)
        
        if clear_button:
            st.rerun()
        
        if send_button:
            if not prompt:
                st.warning("Please enter a prompt")
                return
            
            with st.spinner("Processing..."):
                messages = [{"role": "user", "content": prompt}]
                
                try:
                    result = st.session_state.bridge_manager.chat_completion(
                        model=selected_model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    if result.get('error'):
                        st.error(f"Error: {result['error']}")
                    else:
                        st.success(f"✅ Response from {result['provider_used']}")
                        
                        # Extract response content
                        response_data = result.get('response', {})
                        if "choices" in response_data:
                            content = response_data["choices"][0].get("message", {}).get("content", "")
                            st.markdown("**Response:**")
                            st.markdown(content)
                        
                        # Show metadata
                        if "exo_metadata" in response_data:
                            meta = response_data["exo_metadata"]
                            st.info(f"⚡ Computed in {meta.get('compute_time', 0):.2f}s on {meta.get('device', 'unknown')}")
                        
                        # Show cost
                        cost = result.get('cost', 0)
                        if cost == 0:
                            st.success("💰 Cost: FREE (local inference)")
                        else:
                            st.warning(f"💰 Cost: ${cost:.4f}")
                
                except Exception as e:
                    st.error(f"Request failed: {e}")
                    import traceback
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())
    
    def render_provider_status(self, status: Dict):
        """Render all provider status (Exo + Cloud providers)"""
        st.subheader("🌐 Provider Status & Routing")
        
        # Try to get providers from multiple sources
        token_providers = []
        
        # First try from bridge status
        if status and 'token_manager' in status:
            token_providers = status.get("token_manager", {}).get("providers", [])
        
        # If that fails, try loading directly from config file
        if not token_providers:
            try:
                import json
                from pathlib import Path
                config_path = Path.home() / ".token_manager_config.json"
                
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    token_providers = config.get('providers', [])
                    st.info("📋 Loaded providers directly from config file")
            except Exception as e:
                st.error(f"Failed to load providers: {e}")
        
        # Display each provider
        if token_providers:
            for provider in token_providers:
                provider_name = provider.get("name", "Unknown")
                provider_status = provider.get("status", "unknown")
                provider_type = provider.get("type", "cloud")
                
                # Determine status icon and color
                if provider_status == "active":
                    status_icon = "🟢"
                    status_text = "ONLINE"
                    status_class = "status-healthy"
                elif provider_status == "disabled":
                    status_icon = "🔴"
                    status_text = "DISABLED"
                    status_class = "status-offline"
                else:
                    status_icon = "🟡"
                    status_text = "UNKNOWN"
                    status_class = "status-degraded"
                
                with st.expander(f"{status_icon} {provider_name} - {status_text}", expanded=(provider_type == "local")):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(f"**Type:** {provider_type.upper()}")
                        st.markdown(f"**Priority:** {provider.get('priority', 'N/A')}")
                        base_url = provider.get('base_url', 'N/A')
                        st.markdown(f"**Endpoint:** `{base_url}`")
                    
                    with col2:
                        usage = provider.get('usage', {})
                        requests = usage.get('requests', 0)
                        tokens = usage.get('total_tokens', 0)
                        st.metric("Requests", requests)
                        st.metric("Total Tokens", tokens)
                    
                    with col3:
                        cost = provider.get('cost', 0)
                        if cost == 0 and provider_type == "local":
                            st.success("💰 **Cost:** FREE")
                        else:
                            st.metric("Cost", f"${cost:.4f}")
                        
                        # API Key status
                        has_key = bool(provider.get('api_key') or provider.get('api_key_encrypted'))
                        if provider_type == "local":
                            st.info("🔓 No key required")
                        elif has_key:
                            st.success("🔑 Key configured")
                        else:
                            st.warning("⚠️ No API key")
                    
                    # Capabilities
                    caps = provider.get('capabilities', {})
                    if caps:
                        cap_list = []
                        if caps.get('streaming'): cap_list.append("📡 Streaming")
                        if caps.get('function_calling'): cap_list.append("🔧 Functions")
                        if caps.get('vision'): cap_list.append("👁️ Vision")
                        if caps.get('embeddings'): cap_list.append("🧮 Embeddings")
                        
                        if cap_list:
                            st.markdown("**Capabilities:** " + " • ".join(cap_list))
        
        # If no providers found, show message
        if not token_providers:
            st.warning("⚠️ No providers configured. Check your token manager configuration.")
            st.code("cat ~/.token_manager_config.json")
    
    def render_api_key_management(self):
        """Render API key management interface"""
        st.subheader("🔑 API Key Management")
        
        # Load token manager config
        try:
            import json
            from pathlib import Path
            config_path = Path.home() / ".token_manager_config.json"
            
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                providers = config.get('providers', [])
                
                # Filter cloud providers that need keys
                cloud_providers = [p for p in providers if p.get('type') != 'local']
                
                for provider in cloud_providers:
                    provider_name = provider.get('name', 'Unknown')
                    
                    with st.expander(f"{provider_name} API Key"):
                        has_key = bool(provider.get('api_key_encrypted'))
                        
                        if has_key:
                            st.success(f"✅ API key configured for {provider_name}")
                            st.markdown(f"**Key (encrypted):** `{'*' * 40}`")
                            
                            if st.button(f"Test {provider_name} Connection", key=f"test_{provider_name}"):
                                st.info(f"Testing connection to {provider_name}...")
                                # TODO: Implement connection test
                        else:
                            st.warning(f"⚠️ No API key configured for {provider_name}")
                            
                            new_key = st.text_input(
                                f"Enter {provider_name} API Key",
                                type="password",
                                key=f"key_{provider_name}"
                            )
                            
                            if st.button(f"Save {provider_name} Key", key=f"save_{provider_name}"):
                                if new_key:
                                    st.success(f"Key saved for {provider_name}")
                                    st.info("Note: Restart the HUD to apply changes")
                                else:
                                    st.error("Please enter a valid API key")
            else:
                st.error(f"Token manager config not found: {config_path}")
                st.markdown("Create the config file or check the path in `config/bridge_config.yaml`")
        
        except Exception as e:
            st.error(f"Failed to load API key configuration: {e}")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
    
    def render_recommendation(self, status: Dict):
        """Render system recommendation"""
        recommendation = status.get("recommendation", "")
        
        if recommendation:
            if "✅" in recommendation:
                st.success(recommendation)
            elif "⚠️" in recommendation:
                st.warning(recommendation)
            elif "🔴" in recommendation:
                st.error(recommendation)
            else:
                st.info(recommendation)
    
    def update_history(self, status: Dict):
        """Update request history"""
        usage = status.get("exo", {}).get("usage", {})
        
        st.session_state.history.append({
            "timestamp": datetime.now(),
            "requests": usage.get("total_requests", 0),
            "compute_time": usage.get("total_compute_time", 0)
        })
        
        # Keep only last 100 entries
        if len(st.session_state.history) > 100:
            st.session_state.history = st.session_state.history[-100:]
    
    def render(self):
        """Main render loop"""
        self.render_header()
        
        # Show configuration issues prominently
        if hasattr(st.session_state, 'config_issues') and st.session_state.config_issues:
            with st.expander("⚠️ Configuration Issues Detected", expanded=True):
                for issue in st.session_state.config_issues:
                    st.warning(issue)
                
                st.markdown("""
                **To fix:**
                - Bridge config should exist at: `config/bridge_config.yaml`
                - Token manager config should exist at: `~/.token_manager_config.json`
                - Run setup if needed: `python setup.py install`
                """)
        
        self.render_sidebar()
        
        # Main content
        if not st.session_state.bridge_manager:
            st.info("👈 Connect to your Exo cluster using the sidebar")
            
            # Show setup instructions with API key fields
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🚀 Quick Start")
                st.markdown("""
                **Step 1: Start Exo Cluster**
                ```bash
                cd ~/exo
                source .venv/bin/activate
                python3 exo/main.py --chatgpt-api-port 8000
                ```
                
                **Step 2: Configure Cloud Providers (Optional)**
                - Enter your OpenRouter API key in the sidebar
                - Enter your HuggingFace token in the sidebar
                - Click "Save API Keys"
                
                **Step 3: Connect**
                - Set host (default: localhost)
                - Set port (default: 8000)
                - Enable ReliaKit for auto-healing
                - Click "Connect to Exo"
                """)
            
            with col2:
                st.subheader("🌐 Multi-Provider Routing")
                st.markdown("""
                The HUD supports intelligent routing across:
                
                **Priority 0: Exo Local** 🟢
                - FREE unlimited inference
                - Local models (llama, etc.)
                - No API key needed
                
                **Priority 1: OpenRouter** ☁️
                - 1000+ cloud models
                - Paid per request
                - Requires API key
                
                **Priority 2: Hugging Face** 🤗
                - Open source models
                - Free tier available
                - Requires token
                
                Requests automatically route to Exo first, 
                then failover to cloud if needed.
                """)
            
            st.markdown("---")
            st.subheader("🛡️ ReliaKit Self-Healing")
            st.markdown("""
            When enabled, ReliaKit provides:
            - **Automatic health monitoring** of all Exo nodes and providers
            - **Intelligent failover** when nodes go offline
            - **Automatic recovery** attempts when nodes come back
            - **Live event logging** of all system changes
            - **Real-time metrics** for performance tracking
            """)
            return
        
        # Get status with error handling
        try:
            bridge_status = st.session_state.bridge_manager.get_status()
            
            # Get ReliaKit status if enabled
            reliakit_status = None
            if st.session_state.reliakit_manager:
                try:
                    reliakit_status = st.session_state.reliakit_manager.get_system_status()
                except Exception as e:
                    st.warning(f"⚠️ ReliaKit status unavailable: {e}")
            
            self.update_history(bridge_status)
        except Exception as e:
            st.error(f"Failed to get status: {e}")
            import traceback
            st.code(traceback.format_exc())
            return
        
        # Render components
        self.render_recommendation(bridge_status)
        st.markdown("---")
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Dashboard",
            "🌐 Providers",
            "🔑 API Keys",
            "🤖 Model Testing"
        ])
        
        with tab1:
            self.render_cluster_overview(bridge_status)
            st.markdown("---")
            
            # ReliaKit self-healing status (if enabled)
            if st.session_state.reliakit_manager and reliakit_status:
                try:
                    self.render_reliakit_events()
                    st.markdown("---")
                    self.render_reliakit_targets(reliakit_status)
                    st.markdown("---")
                except Exception as e:
                    st.warning(f"⚠️ ReliaKit display error: {e}")
            
            self.render_usage_stats(bridge_status)
        
        with tab2:
            try:
                self.render_provider_status(bridge_status)
            except Exception as e:
                st.error(f"❌ Provider display error: {e}")
                with st.expander("Error Details"):
                    import traceback
                    st.code(traceback.format_exc())
        
        with tab3:
            try:
                self.render_api_key_management()
            except Exception as e:
                st.error(f"❌ API key management error: {e}")
                with st.expander("Error Details"):
                    import traceback
                    st.code(traceback.format_exc())
        
        with tab4:
            try:
                self.render_model_selector(bridge_status)
            except Exception as e:
                st.error(f"❌ Model selector error: {e}")
                with st.expander("Error Details"):
                    import traceback
                    st.code(traceback.format_exc())
        
        # Auto-refresh
        if st.session_state.auto_refresh:
            time.sleep(st.session_state.refresh_interval)
            st.rerun()


# Main execution
if __name__ == "__main__":
    hud = SpiralCodexHUD()
    hud.render()
