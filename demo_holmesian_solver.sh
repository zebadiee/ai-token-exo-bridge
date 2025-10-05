#!/bin/bash
echo "Holmesian Autocorrection Layer - Demo"
echo "====================================="
cd "$(dirname "$0")"
[ -f ".venv/bin/activate" ] && source .venv/bin/activate
python src/holmesian_solver.py
echo ""
echo "Try the UI: streamlit run src/holmesian_ui.py"
