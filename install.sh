#!/bin/bash
set -e

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Installing Playwright browser binaries..."
playwright install chromium

echo "Done!"
