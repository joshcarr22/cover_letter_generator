#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers in user space
export PLAYWRIGHT_BROWSERS_PATH=$HOME/.cache/ms-playwright
python -m playwright install chromium --with-deps 