#!/bin/bash
# Create GitHub repo and push - zebadiee/ai-token-exo-bridge

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Creating and Pushing ai-token-exo-bridge to GitHub         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

cd ~/ai-token-exo-bridge

# Check if gh CLI is available
if command -v gh &> /dev/null; then
    echo "✓ GitHub CLI found"
    echo ""
    echo "Creating repository on GitHub..."
    
    gh repo create zebadiee/ai-token-exo-bridge \
        --public \
        --description "Self-healing AI infrastructure bridging ai-token-manager with Exo distributed cluster" \
        --source=. \
        --push
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "╔══════════════════════════════════════════════════════════════╗"
        echo "║  ✅ Repository created and pushed!                          ║"
        echo "╚══════════════════════════════════════════════════════════════╝"
        echo ""
        echo "View at: https://github.com/zebadiee/ai-token-exo-bridge"
        echo ""
    fi
else
    echo "❌ GitHub CLI (gh) not found"
    echo ""
    echo "Please either:"
    echo ""
    echo "Option 1: Install GitHub CLI"
    echo "  brew install gh"
    echo "  gh auth login"
    echo "  ./CREATE_AND_PUSH.sh"
    echo ""
    echo "Option 2: Create manually"
    echo "  1. Go to: https://github.com/new"
    echo "  2. Name: ai-token-exo-bridge"
    echo "  3. Description: Self-healing AI infrastructure bridging ai-token-manager with Exo distributed cluster"
    echo "  4. Visibility: Public"
    echo "  5. Do NOT initialize with README"
    echo "  6. Click 'Create repository'"
    echo "  7. Then run: git push -u origin master"
    echo ""
fi
