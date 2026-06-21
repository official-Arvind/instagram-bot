#!/bin/bash
echo "===================================================="
echo "  Instagram Bot - macOS/Linux One-Click Setup"
echo "===================================================="
echo ""

# Ensure we have Python 3 installed
if ! command -v python3 &> /dev/null
then
    echo "ERROR: python3 could not be found. Please install Python 3 and try again."
    exit 1
fi

echo "Creating virtual environment..."
python3 -m venv venv

if [ ! -d "venv" ]; then
    echo "ERROR: Failed to create virtual environment."
    exit 1
fi

echo "Installing dependencies..."
./venv/bin/pip install -r requirements.txt --quiet

echo ""
echo "===================================================="
echo "  Setup complete! Start the bot by running: ./run.sh"
echo "===================================================="
