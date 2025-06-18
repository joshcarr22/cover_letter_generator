#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright and its browser dependencies
playwright install chromium
playwright install-deps 