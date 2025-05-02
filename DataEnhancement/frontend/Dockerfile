FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy app files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose default Streamlit port
EXPOSE 8501

# Start Streamlit with main.py
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
