@echo off

echo 🔧 Setting up Python virtual environment...
python -m venv .venv
call .venv\Scripts\activate

echo 📦 Installing dependencies...
pip install --upgrade pip
pip install -r DataEnhancement\backend\requirements.txt

echo 🚀 Launching backend Flask API...
start /B python DataEnhancement\backend\api.py

echo 🌐 Launching Streamlit frontend...
streamlit run DataEnhancement\frontend\main.py
