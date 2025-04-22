#!/bin/bash

echo "🔧 Setting up Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r DataEnhancement/backend/requirements.txt

echo "🚀 Launching backend Flask API..."
nohup python3 DataEnhancement/backend/api.py > backend.log 2>&1 &

echo "🌐 Launching Streamlit frontend..."
streamlit run DataEnhancement/frontend/main.py
