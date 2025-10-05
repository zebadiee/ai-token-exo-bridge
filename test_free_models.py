#!/usr/bin/env python3
"""
Test OpenRouter Free Models API

This script connects to OpenRouter, fetches all models with pricing,
and displays which ones are truly free (both prompt and completion = $0.00).

Run this to see EXACTLY which models are free right now.
"""

import requests
import json
import sys
from typing import List, Dict, Tuple

OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"


def fetch_models_with_pricing(api_key: str) -> List[Dict]:
    """
    Fetch all models from OpenRouter API with pricing information
    
    Returns:
        List of models with full pricing details
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "spiral-codex-hud",
        "X-Title": "Spiral Codex HUD"
    }
    
    try:
        print("🔍 Fetching models from OpenRouter API...")
        response = requests.get(
            f"{OPENROUTER_API_BASE}/models",
            headers=headers,
            timeout=15
        )
        
        if response.status_code != 200:
            print(f"❌ API Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return []
        
        data = response.json()
        models = data.get('data', [])
        
        print(f"✅ Fetched {len(models)} total models\n")
        return models
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def parse_pricing(model_data: Dict) -> Tuple[float, float, bool]:
    """
    Parse pricing information from model data
    
    Returns:
        (prompt_cost, completion_cost, is_free)
    """
    pricing = model_data.get('pricing', {})
    
    # Handle string prices with $ sign
    prompt_str = str(pricing.get('prompt', '0'))
    completion_str = str(pricing.get('completion', '0'))
    
    # Remove $ and convert to float
    try:
        prompt_cost = float(prompt_str.replace('$', '').strip())
        completion_cost = float(completion_str.replace('$', '').strip())
    except:
        prompt_cost = float('inf')  # Unknown cost = treat as paid
        completion_cost = float('inf')
    
    is_free = (prompt_cost == 0.0 and completion_cost == 0.0)
    
    return prompt_cost, completion_cost, is_free


def analyze_models(models: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Analyze models and separate free from paid
    
    Returns:
        (free_models, paid_models)
    """
    free_models = []
    paid_models = []
    
    for model in models:
        model_id = model.get('id', 'unknown')
        name = model.get('name', model_id)
        context_length = model.get('context_length', 0)
        
        prompt_cost, completion_cost, is_free = parse_pricing(model)
        
        model_info = {
            'id': model_id,
            'name': name,
            'context_length': context_length,
            'prompt_cost': prompt_cost,
            'completion_cost': completion_cost,
            'is_free': is_free,
            'has_free_label': ':free' in model_id.lower()
        }
        
        if is_free:
            free_models.append(model_info)
        else:
            paid_models.append(model_info)
    
    return free_models, paid_models


def print_report(free_models: List[Dict], paid_models: List[Dict]):
    """Print comprehensive free models report"""
    
    print("=" * 80)
    print("OPENROUTER FREE MODELS REPORT")
    print("=" * 80)
    print()
    
    # Summary
    total = len(free_models) + len(paid_models)
    print(f"📊 Summary:")
    print(f"   Total Models: {total}")
    print(f"   Free Models: {len(free_models)} ({len(free_models)/total*100:.1f}%)")
    print(f"   Paid Models: {len(paid_models)} ({len(paid_models)/total*100:.1f}%)")
    print()
    
    # Free models detail
    if free_models:
        print("=" * 80)
        print("✅ FREE MODELS (Prompt: $0.00 | Completion: $0.00)")
        print("=" * 80)
        print()
        
        # Group by has :free label
        labeled_free = [m for m in free_models if m['has_free_label']]
        unlabeled_free = [m for m in free_models if not m['has_free_label']]
        
        if labeled_free:
            print(f"🏷️  Models with ':free' label ({len(labeled_free)}):")
            print("-" * 80)
            for model in sorted(labeled_free, key=lambda m: m['name']):
                print(f"   ✓ {model['name']}")
                print(f"     ID: {model['id']}")
                print(f"     Context: {model['context_length']:,} tokens")
                print(f"     Pricing: Prompt=$0.00, Completion=$0.00")
                print()
        
        if unlabeled_free:
            print(f"💎 Free models WITHOUT ':free' label ({len(unlabeled_free)}):")
            print("-" * 80)
            print("⚠️  These are free but not obviously labeled:")
            print()
            for model in sorted(unlabeled_free, key=lambda m: m['name']):
                print(f"   ✓ {model['name']}")
                print(f"     ID: {model['id']}")
                print(f"     Context: {model['context_length']:,} tokens")
                print(f"     Pricing: Prompt=$0.00, Completion=$0.00")
                print()
    else:
        print("❌ No free models found!")
        print()
    
    # Sample paid models for reference
    if paid_models:
        print("=" * 80)
        print("💰 SAMPLE PAID MODELS (for reference)")
        print("=" * 80)
        print()
        
        # Show a few examples
        sample_paid = sorted(paid_models, key=lambda m: m['prompt_cost'])[:5]
        
        for model in sample_paid:
            print(f"   • {model['name']}")
            print(f"     ID: {model['id']}")
            print(f"     Pricing: Prompt=${model['prompt_cost']:.6f}, Completion=${model['completion_cost']:.6f}")
            print()
        
        if len(paid_models) > 5:
            print(f"   ... and {len(paid_models) - 5} more paid models")
            print()
    
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()
    print("✅ SAFE TO USE (100% Free):")
    print()
    
    if free_models:
        # Recommend top 5 by context length
        top_free = sorted(free_models, key=lambda m: m['context_length'], reverse=True)[:5]
        for idx, model in enumerate(top_free, 1):
            label = " (HAS :free LABEL)" if model['has_free_label'] else ""
            print(f"   {idx}. {model['name']}{label}")
            print(f"      → Use ID: {model['id']}")
            print(f"      → Context: {model['context_length']:,} tokens")
            print()
    else:
        print("   ⚠️  No free models currently available")
        print()
    
    print("=" * 80)
    print()


def save_free_models_list(free_models: List[Dict], output_file: str = "free_models_verified.json"):
    """Save verified free models to JSON file"""
    try:
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': str(__import__('datetime').datetime.now()),
                'count': len(free_models),
                'models': free_models
            }, f, indent=2)
        
        print(f"💾 Saved verified free models to: {output_file}")
        print()
        
    except Exception as e:
        print(f"❌ Failed to save file: {e}")


def main():
    """Main execution"""
    if len(sys.argv) < 2:
        print("=" * 80)
        print("OPENROUTER FREE MODELS TESTER")
        print("=" * 80)
        print()
        print("Usage:")
        print("  python test_free_models.py YOUR_OPENROUTER_API_KEY")
        print()
        print("Example:")
        print("  python test_free_models.py sk-or-v1-abc123...")
        print()
        print("This will:")
        print("  1. Fetch all OpenRouter models with pricing")
        print("  2. Identify truly free models ($0.00 for both prompt and completion)")
        print("  3. Show which models have ':free' labels")
        print("  4. Recommend safe models to use")
        print("  5. Save verified free models list")
        print()
        sys.exit(1)
    
    api_key = sys.argv[1]
    
    # Fetch models
    models = fetch_models_with_pricing(api_key)
    
    if not models:
        print("❌ Could not fetch models. Check your API key and connection.")
        sys.exit(1)
    
    # Analyze
    free_models, paid_models = analyze_models(models)
    
    # Print report
    print_report(free_models, paid_models)
    
    # Save verified free models
    if free_models:
        save_free_models_list(free_models)
    
    print("✅ Analysis complete!")
    print()
    print("Next Steps:")
    print("  1. Use the recommended free models above")
    print("  2. Update your UI to filter for these models only")
    print("  3. Check free_models_verified.json for the complete list")
    print()


if __name__ == "__main__":
    main()
