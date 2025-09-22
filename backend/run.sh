#!/bin/bash

# Navigate to the backend directory
cd "$(dirname "$0")"

# Activate the virtual environment (assuming it's in the project root)
source ../venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Run the Flask app
python app.py
