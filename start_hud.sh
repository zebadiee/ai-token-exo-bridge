#!/bin/bash
# Simple HUD-only startup script
# Assumes Exo is already running

cd ~/ai-token-exo-bridge
source .venv/bin/activate
streamlit run src/spiral_codex_hud.py
