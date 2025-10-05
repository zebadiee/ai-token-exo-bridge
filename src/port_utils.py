#!/usr/bin/env python3
"""
Port utilities for automatic port conflict resolution
"""

import socket
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def is_port_available(port: int, host: str = "localhost") -> bool:
    """
    Check if a port is available for use
    
    Args:
        port: Port number to check
        host: Host to check on (default: localhost)
    
    Returns:
        True if port is available, False if in use
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    
    try:
        sock.bind((host, port))
        sock.close()
        return True
    except (socket.error, OSError):
        return False


def find_available_port(
    preferred_port: int,
    host: str = "localhost",
    port_range: int = 100,
    exclude_ports: Optional[List[int]] = None
) -> int:
    """
    Find an available port, starting with preferred port
    
    Args:
        preferred_port: First port to try
        host: Host to bind on
        port_range: How many ports to try after preferred
        exclude_ports: Ports to skip
    
    Returns:
        Available port number
    
    Raises:
        RuntimeError: If no available port found in range
    """
    exclude_ports = exclude_ports or []
    
    # Try preferred port first
    if preferred_port not in exclude_ports and is_port_available(preferred_port, host):
        logger.info(f"Using preferred port {preferred_port}")
        return preferred_port
    
    # Try sequential ports
    for offset in range(1, port_range + 1):
        port = preferred_port + offset
        
        if port > 65535:  # Max port number
            break
        
        if port in exclude_ports:
            continue
        
        if is_port_available(port, host):
            logger.info(f"Port {preferred_port} in use, using alternative port {port}")
            return port
    
    raise RuntimeError(
        f"No available port found in range {preferred_port}-{preferred_port + port_range}"
    )


def get_port_info(port: int, host: str = "localhost") -> dict:
    """
    Get information about a port
    
    Args:
        port: Port to check
        host: Host to check
    
    Returns:
        Dict with port status information
    """
    available = is_port_available(port, host)
    
    info = {
        "port": port,
        "host": host,
        "available": available,
        "status": "available" if available else "in_use"
    }
    
    # Try to get process info if port is in use (macOS/Linux)
    if not available:
        try:
            import subprocess
            result = subprocess.run(
                ["lsof", "-i", f":{port}", "-sTCP:LISTEN"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    # Parse lsof output
                    parts = lines[1].split()
                    if len(parts) > 1:
                        info["process"] = parts[0]
                        info["pid"] = parts[1]
        except Exception:
            pass  # lsof not available or failed
    
    return info


def kill_port_process(port: int, force: bool = False) -> bool:
    """
    Kill process using a port (use with caution!)
    
    Args:
        port: Port whose process to kill
        force: Use SIGKILL instead of SIGTERM
    
    Returns:
        True if successful, False otherwise
    """
    try:
        import subprocess
        import signal
        
        # Get PID
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.stdout:
            pid = result.stdout.strip()
            sig = signal.SIGKILL if force else signal.SIGTERM
            
            logger.warning(f"Killing process {pid} on port {port}")
            subprocess.run(["kill", f"-{sig.value}", pid], timeout=2)
            return True
        
        return False
    
    except Exception as e:
        logger.error(f"Failed to kill process on port {port}: {e}")
        return False


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Check port
    port = 8501
    info = get_port_info(port)
    print(f"Port {port} status: {info}")
    
    # Find available port
    available = find_available_port(8501, port_range=50)
    print(f"Available port: {available}")
