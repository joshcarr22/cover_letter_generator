#!/usr/bin/env bash
# exit on error
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Install pyppeteer and its dependencies
pip install pyppeteer
python -c "import pyppeteer.chromium_downloader; pyppeteer.chromium_downloader.download_chromium()"

# Test the health endpoint
curl https://cover-letter-generator-2.onrender.com/health 