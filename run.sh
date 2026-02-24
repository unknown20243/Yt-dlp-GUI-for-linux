#!/bin/bash
# Check if venv exists, if not, create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the GUI
echo "Starting yt-dlp GUI..."
python yt_dlp_gui.py
