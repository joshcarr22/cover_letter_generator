#!/usr/bin/env bash
# exit on error
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Download Chromium for pyppeteer
python -c "import pyppeteer; pyppeteer.install()"

# Optional: Ping health check (use your actual app URL)
curl https://cover-letter-generator-2.onrender.com/health || true
