#!/bin/bash
# Quick dependency installer for AI Token Manager + Exo Bridge
# Handles virtual environment setup and all dependencies

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AI Token Manager + Exo Bridge - Dependency Installer       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}1. Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_MAJOR=3
REQUIRED_MINOR=12

ACTUAL_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
ACTUAL_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$ACTUAL_MAJOR" -lt "$REQUIRED_MAJOR" ] || ([ "$ACTUAL_MAJOR" -eq "$REQUIRED_MAJOR" ] && [ "$ACTUAL_MINOR" -lt "$REQUIRED_MINOR" ]); then
    echo -e "${RED}✗ Python 3.12+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"
echo ""

# Create virtual environment
echo -e "${YELLOW}2. Setting up virtual environment...${NC}"
if [ -d "$SCRIPT_DIR/.venv" ]; then
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
else
    python3 -m venv "$SCRIPT_DIR/.venv"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi
echo ""

# Activate virtual environment
echo -e "${YELLOW}3. Activating virtual environment...${NC}"
source "$SCRIPT_DIR/.venv/bin/activate"
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo -e "${YELLOW}4. Upgrading pip...${NC}"
pip install --upgrade pip --quiet
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Install dependencies
echo -e "${YELLOW}5. Installing dependencies (this may take a minute)...${NC}"
pip install -r "$SCRIPT_DIR/requirements.txt" --quiet
echo -e "${GREEN}✓ All dependencies installed${NC}"
echo ""

# Verify key packages
echo -e "${YELLOW}6. Verifying installation...${NC}"
python3 << 'PYTHON_CHECK'
import sys
packages = ['streamlit', 'plotly', 'pandas', 'requests', 'yaml']
missing = []

for pkg in packages:
    try:
        __import__(pkg)
        print(f"✓ {pkg}")
    except ImportError:
        missing.append(pkg)
        print(f"✗ {pkg}")

if missing:
    print(f"\nMissing packages: {', '.join(missing)}")
    sys.exit(1)
else:
    print("\n✓ All critical packages verified")
PYTHON_CHECK

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ Installation Complete!                                    ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Next steps:"
echo "  1. Ensure Exo is installed: ~/exo"
echo "  2. Launch the stack: ./launch.sh"
echo "  3. Access HUD: http://localhost:8501"
echo ""
echo "Virtual environment activated. To activate it manually later:"
echo "  source .venv/bin/activate"
echo ""
