#!/usr/bin/env bash
# exit on error
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Run health check
curl https://cover-letter-generator-2.onrender.com/health
