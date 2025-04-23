FROM debian:bullseye

# 📦 Install base dependencies for Playwright + Chromium
RUN apt-get update && apt-get install -y \
    python3 python3-pip curl gnupg unzip wget software-properties-common \
    fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 \
    libc6 libcairo2 libcups2 libcurl4 libdbus-1-3 libexpat1 libgbm1 libglib2.0-0 \
    libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 libudev1 libvulkan1 libx11-6 \
    libxcb1 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxkbcommon0 \
    libxrandr2 xdg-utils patch build-essential gcc --no-install-recommends && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


# 🐍 Python setup
COPY requirements.txt .
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt
RUN pip3 install playwright && playwright install chromium

# 📁 Copy app code
COPY . .

# 🌍 Environment variables
ENV CHROME_BIN=/usr/bin/chromium
ENV USER_DATA_DIR=/tmp/.linkedin_profile
ENV PYTHONPATH=/app

WORKDIR /app

# 🎯 Expose Streamlit port
EXPOSE 8501

# 🚀 Launch Streamlit
CMD ["streamlit", "run", "/frontend/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
