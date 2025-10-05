#!/bin/bash
# Push ai-token-exo-bridge to GitHub (zebadiee)

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Pushing ai-token-exo-bridge to GitHub                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Add remote
echo "Adding GitHub remote..."
git remote add origin https://github.com/zebadiee/ai-token-exo-bridge.git 2>/dev/null || echo "Remote already exists"

# Show what will be pushed
echo ""
echo "Commits to push:"
git log --oneline origin/master..HEAD 2>/dev/null || git log --oneline

echo ""
echo "Files to push:"
git ls-files | wc -l | xargs echo "Total files:"

echo ""
read -p "Push to GitHub? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Pushing to GitHub..."
    git push -u origin master
    
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "View at: https://github.com/zebadiee/ai-token-exo-bridge"
    echo ""
else
    echo "Push cancelled."
fi
