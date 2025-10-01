#!/bin/bash
# Setup script for Bandcamp Wishlist Automator

echo "=================================="
echo "Bandcamp Automator Setup"
echo "=================================="
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv_bandcamp

# Activate it
echo "Activating virtual environment..."
source venv_bandcamp/bin/activate

# Install selenium
echo "Installing selenium..."
pip install selenium

echo ""
echo "✓ Setup complete!"
echo ""
echo "To run the script:"
echo "  1. Activate the environment: source venv_bandcamp/bin/activate"
echo "  2. Run the script: python bandcamp_wishlist_automator.py"
echo ""
echo "Note: You also need ChromeDriver installed:"
echo "  brew install chromedriver"
echo ""
