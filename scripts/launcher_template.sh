#!/bin/zsh

# ----------------------------------------
# Bridge Game Finder launcher
# ----------------------------------------

PROJECT_DIR="$HOME/Casual_claude/Bridge_Club_Games"

cd "$PROJECT_DIR" || { echo "Could not cd to $PROJECT_DIR"; exec zsh -i; }

[[ -f "$HOME/.zshrc" ]] && source "$HOME/.zshrc"
[[ -f ".venv/bin/activate" ]] && source ".venv/bin/activate"

python3 scripts/bridge_finder.py

echo ""
echo "=== Done. Press Ctrl-D or type 'exit' to close. ==="
exec zsh -i
