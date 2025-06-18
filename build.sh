#!/usr/bin/env bash
# exit on error
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Download Chromium for pyppeteer (correct modern way)
python -c "import pyppeteer.chromium_downloader as d; d.download_chromium()"

# Test the health endpoint (optional)
curl https://cover-letter-generator-2.onrender.com/health || true
