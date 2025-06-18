#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Install pyppeteer browser
python -c "import pyppeteer.chromium_downloader; pyppeteer.chromium_downloader.download_chromium()"

# Test the health endpoint
curl https://cover-letter-generator-2.onrender.com/health 