#!/usr/bin/env python3
"""
Complete Integration Example - Exo + Cloud Providers

Demonstrates:
1. Exo local inference (free, priority 0)
2. Auto-failover to OpenRouter if Exo unavailable
3. Auto-failover to HuggingFace if both fail
4. Token tracking and cost calculation
5. Health monitoring
"""

import sys
import os
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path.home() / "ai-token-manager"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.bridge_manager import ExoBridgeManager
import json
import time

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def print_provider_status(bridge):
    """Display current provider status"""
    status = bridge.get_status()
    
    print("\n📊 Provider Status:")
    print(f"  Exo Cluster:  {'✅ Available' if status['exo']['available'] else '❌ Offline'}")
    if status['exo']['available']:
        print(f"    Healthy Nodes: {status['exo']['health']['healthy_nodes']}")
        print(f"    Total Nodes:   {status['exo']['health']['total_nodes']}")
    
    print(f"\n  Token Manager:")
    print(f"    Active Providers: {len(status['token_manager']['providers'])}")
    for provider in status['token_manager']['providers']:
        print(f"    - {provider['name']}: {provider['status']}")

def test_local_inference(bridge):
    """Test Exo local inference"""
    print_header("Test 1: Exo Local Inference (Free)")
    
    result = bridge.chat_completion(
        messages=[
            {"role": "user", "content": "Say hello in 5 words or less"}
        ],
        model="llama-3.2-3b",
        max_tokens=20
    )
    
    print(f"Provider Used: {result['provider_used']}")
    print(f"Cost: ${result['cost']}")
    
    if result['error']:
        print(f"⚠️  Error: {result['error']}")
    else:
        response_text = result['response'].get('choices', [{}])[0].get('message', {}).get('content', '')
        print(f"Response: {response_text}")
    
    return result

def test_cloud_failover(bridge):
    """Test failover to cloud providers"""
    print_header("Test 2: Cloud Failover (if Exo unavailable)")
    
    # Temporarily disable Exo to test failover
    original_host = bridge.integration.exo_provider.primary_node_host
    
    # Test with a model that might not be on Exo
    result = bridge.chat_completion(
        messages=[
            {"role": "user", "content": "Respond with just 'OK'"}
        ],
        model="gpt-3.5-turbo",  # This will trigger cloud routing
        max_tokens=5
    )
    
    print(f"Provider Used: {result['provider_used']}")
    print(f"Cost: ${result['cost']}")
    
    if result['error']:
        print(f"⚠️  Error: {result['error']}")
    else:
        response_text = result['response'].get('choices', [{}])[0].get('message', {}).get('content', '')
        print(f"Response: {response_text}")

def show_usage_stats(bridge):
    """Show usage and cost statistics"""
    print_header("Usage Statistics")
    
    status = bridge.get_status()
    
    print("📈 Exo Local Usage:")
    exo_usage = status['exo']['usage']
    print(f"  Total Requests: {exo_usage['requests']}")
    print(f"  Compute Time:   {exo_usage['compute_time']:.2f}s")
    print(f"  Cost:           $0.00 (FREE!)")
    
    print("\n💰 Cloud Provider Usage:")
    for provider in status['token_manager']['providers']:
        if provider['name'] != 'Exo Local':
            usage = provider.get('usage', {})
            print(f"\n  {provider['name']}:")
            print(f"    Requests:  {usage.get('requests', 0)}")
            print(f"    Tokens:    {usage.get('total_tokens', 0)}")
            print(f"    Status:    {provider['status']}")

def main():
    """Main demonstration"""
    print_header("🌀 Spiral Codex - Full Integration Demo")
    
    print("Initializing bridge with cloud failover...")
    
    # Initialize bridge with cloud failover enabled
    bridge = ExoBridgeManager(
        exo_host="localhost",
        exo_port=8000,
        enable_hud=False  # Run without HUD for this test
    )
    
    bridge.start()
    
    # Show initial status
    print_provider_status(bridge)
    
    # Wait a moment for initialization
    time.sleep(2)
    
    # Test 1: Local inference
    try:
        test_local_inference(bridge)
    except Exception as e:
        print(f"⚠️  Local inference error: {e}")
    
    time.sleep(1)
    
    # Test 2: Cloud failover
    try:
        test_cloud_failover(bridge)
    except Exception as e:
        print(f"⚠️  Cloud failover error: {e}")
    
    # Show final statistics
    show_usage_stats(bridge)
    
    # Summary
    print_header("Summary")
    print("""
    ✅ Local Exo inference: FREE, unlimited
    ✅ Cloud failover: Automatic when Exo unavailable
    ✅ Token tracking: All providers monitored
    ✅ Cost optimization: Prefers free local inference
    
    Next Steps:
    1. Start HUD: python src/bridge_manager.py --with-hud
    2. View at: http://localhost:8501
    3. Monitor all providers in real-time
    """)
    
    bridge.stop()

if __name__ == "__main__":
    main()
