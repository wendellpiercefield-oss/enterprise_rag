#!/bin/bash

echo "Creating virtual environment..."
python -m venv .venv

echo "Activating environment..."
source .venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setting up database..."
psql -U postgres -d knowledge -f backend/database/init.sql

echo "Setup complete."