#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers without requiring root
export PLAYWRIGHT_BROWSERS_PATH=0
playwright install --with-deps chromium 