FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    chromium chromium-driver unzip curl gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Environment variables for Chrome path
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Set workdir
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app
COPY . .

# Run your API (adjust if using something like Flask)
CMD ["python", "api.py"]
