#!/usr/bin/env python3
"""
Localhost Exo Node Auto-Detection

Automatically detects and enables local Exo cluster nodes.

Features:
- Scans common ports for Exo nodes
- Tests connectivity and health
- Auto-enables in provider config
- UI integration for manual rescan
"""

import requests
import socket
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class LocalNodeInfo:
    """Information about a detected local node"""
    host: str
    port: int
    url: str
    healthy: bool
    node_type: str
    version: Optional[str] = None
    models_available: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'host': self.host,
            'port': self.port,
            'url': self.url,
            'healthy': self.healthy,
            'node_type': self.node_type,
            'version': self.version,
            'models_available': self.models_available
        }


class LocalhostAutoDetector:
    """
    Auto-detect local Exo cluster nodes
    
    Scans common ports and validates connectivity
    """
    
    # Common ports to scan for Exo nodes
    COMMON_PORTS = [
        8000,  # Exo default
        8001,
        8080,
        8888,
        5000,
        5001
    ]
    
    # Health check endpoints to try
    HEALTH_ENDPOINTS = [
        '/health',
        '/v1/models',
        '/api/health',
        '/status',
        '/'
    ]
    
    def __init__(self, timeout: float = 2.0):
        """
        Initialize auto-detector
        
        Args:
            timeout: Timeout for connection tests (seconds)
        """
        self.timeout = timeout
        self.detected_nodes: List[LocalNodeInfo] = []
    
    def scan_localhost(self, ports: Optional[List[int]] = None) -> List[LocalNodeInfo]:
        """
        Scan localhost for Exo nodes
        
        Args:
            ports: Optional list of ports to scan (default: COMMON_PORTS)
            
        Returns:
            List of detected nodes
        """
        ports = ports or self.COMMON_PORTS
        detected = []
        
        logger.info(f"Scanning localhost ports: {ports}")
        
        for port in ports:
            node_info = self._test_port(port)
            if node_info:
                detected.append(node_info)
                logger.info(f"✅ Detected node at {node_info.url}")
        
        self.detected_nodes = detected
        logger.info(f"Scan complete: {len(detected)} nodes detected")
        
        return detected
    
    def _test_port(self, port: int) -> Optional[LocalNodeInfo]:
        """
        Test if a port has an Exo node
        
        Args:
            port: Port to test
            
        Returns:
            LocalNodeInfo if node found, None otherwise
        """
        # First check if port is open
        if not self._is_port_open('127.0.0.1', port):
            return None
        
        # Try health endpoints
        base_url = f"http://127.0.0.1:{port}"
        
        for endpoint in self.HEALTH_ENDPOINTS:
            url = f"{base_url}{endpoint}"
            
            try:
                response = requests.get(url, timeout=self.timeout)
                
                if response.status_code == 200:
                    # Found a responding endpoint
                    node_type = self._identify_node_type(response, endpoint)
                    
                    # Try to get more info
                    version, models_count = self._get_node_details(base_url)
                    
                    return LocalNodeInfo(
                        host='127.0.0.1',
                        port=port,
                        url=base_url,
                        healthy=True,
                        node_type=node_type,
                        version=version,
                        models_available=models_count
                    )
                    
            except requests.RequestException:
                continue
        
        return None
    
    def _is_port_open(self, host: str, port: int) -> bool:
        """Check if a port is open"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        
        try:
            result = sock.connect_ex((host, port))
            return result == 0
        except socket.error:
            return False
        finally:
            sock.close()
    
    def _identify_node_type(self, response: requests.Response, endpoint: str) -> str:
        """Identify the type of node from response"""
        try:
            data = response.json()
            
            # Check for Exo-specific fields
            if 'exo' in str(data).lower():
                return 'Exo Cluster'
            
            # Check for model list (common in LLM APIs)
            if 'models' in data or 'data' in data:
                return 'Exo Cluster'
            
            # Check endpoint
            if '/v1/models' in endpoint:
                return 'Exo Cluster'
            
            return 'Local Node'
            
        except:
            return 'Local Node'
    
    def _get_node_details(self, base_url: str) -> Tuple[Optional[str], int]:
        """
        Get additional node details
        
        Returns:
            (version, models_count)
        """
        version = None
        models_count = 0
        
        # Try to get models
        try:
            response = requests.get(
                f"{base_url}/v1/models",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Count models
                if 'data' in data:
                    models_count = len(data['data'])
                elif 'models' in data:
                    models_count = len(data['models'])
                
                # Try to get version
                if 'version' in data:
                    version = data['version']
                    
        except:
            pass
        
        return version, models_count
    
    def get_best_node(self) -> Optional[LocalNodeInfo]:
        """Get the best detected node (most models, lowest port)"""
        if not self.detected_nodes:
            return None
        
        # Sort by models available (desc), then port (asc)
        sorted_nodes = sorted(
            self.detected_nodes,
            key=lambda n: (-n.models_available, n.port)
        )
        
        return sorted_nodes[0]
    
    def enable_in_config(self, node: LocalNodeInfo, config_path: str) -> bool:
        """
        Enable detected node in provider config
        
        Args:
            node: Node to enable
            config_path: Path to config file
            
        Returns:
            True if successful
        """
        import json
        from pathlib import Path
        
        try:
            # Load config
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Find or create Exo provider
            providers = config.get('providers', [])
            exo_provider = None
            
            for provider in providers:
                if 'exo' in provider.get('name', '').lower():
                    exo_provider = provider
                    break
            
            if not exo_provider:
                # Create new provider entry
                exo_provider = {
                    'name': 'Exo Local',
                    'type': 'local',
                    'auto_detected': True
                }
                providers.append(exo_provider)
                config['providers'] = providers
            
            # Update provider config
            exo_provider.update({
                'base_url': node.url,
                'models_endpoint': 'v1/models',
                'chat_endpoint': 'v1/chat/completions',
                'status': 'active',
                'auto_detected': True,
                'detected_at': __import__('datetime').datetime.now().isoformat(),
                'port': node.port,
                'models_available': node.models_available
            })
            
            # Save config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Enabled Exo Local at {node.url} in config")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            return False


# Streamlit UI Integration
def streamlit_localhost_detector():
    """Streamlit widget for localhost detection"""
    import streamlit as st
    
    detector = LocalhostAutoDetector()
    
    st.subheader("🔍 Localhost Node Detection")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("Automatically detect local Exo cluster nodes")
    
    with col2:
        if st.button("🔄 Scan Now", key="scan_localhost"):
            with st.spinner("Scanning localhost..."):
                nodes = detector.scan_localhost()
                
                if nodes:
                    st.success(f"✅ Found {len(nodes)} node(s)!")
                else:
                    st.warning("No local nodes detected")
    
    # Show detected nodes
    if detector.detected_nodes:
        st.markdown("**Detected Nodes:**")
        
        for node in detector.detected_nodes:
            with st.expander(f"📍 {node.node_type} - Port {node.port}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**URL:** {node.url}")
                    st.write(f"**Status:** {'✅ Healthy' if node.healthy else '❌ Unhealthy'}")
                    st.write(f"**Type:** {node.node_type}")
                
                with col2:
                    st.write(f"**Port:** {node.port}")
                    st.write(f"**Models:** {node.models_available}")
                    if node.version:
                        st.write(f"**Version:** {node.version}")
                
                if st.button(f"Enable This Node", key=f"enable_{node.port}"):
                    from pathlib import Path
                    config_path = Path.home() / ".token_manager_config.json"
                    
                    if detector.enable_in_config(node, str(config_path)):
                        st.success(f"✅ Enabled {node.node_type} at {node.url}")
                        st.rerun()
                    else:
                        st.error("Failed to enable node")
    
    return detector.detected_nodes


if __name__ == "__main__":
    # Test the detector
    detector = LocalhostAutoDetector()
    
    print("🔍 Scanning for local nodes...")
    nodes = detector.scan_localhost()
    
    print(f"\n✅ Detected {len(nodes)} node(s):")
    for node in nodes:
        print(f"\n  {node.node_type}")
        print(f"    URL: {node.url}")
        print(f"    Models: {node.models_available}")
        print(f"    Healthy: {node.healthy}")
    
    if nodes:
        best = detector.get_best_node()
        print(f"\n🏆 Best node: {best.url}")
