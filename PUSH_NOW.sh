#!/bin/bash
# Quick push to GitHub - zebadiee/ai-token-exo-bridge

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Pushing to github.com/zebadiee/ai-token-exo-bridge         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

cd ~/ai-token-exo-bridge

echo "Repository status:"
git status --short
echo ""

echo "Commits to push:"
git log --oneline -5
echo ""

echo "Remote:"
git remote -v
echo ""

echo "Pushing to GitHub..."
git push -u origin master

if [ $? -eq 0 ]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  ✅ Successfully pushed to GitHub!                          ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "View at: https://github.com/zebadiee/ai-token-exo-bridge"
    echo ""
else
    echo ""
    echo "⚠️  Push failed. You may need to:"
    echo "1. Create the repository at https://github.com/new"
    echo "2. Authenticate with GitHub (gh auth login or SSH keys)"
    echo ""
fi
