FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg \
    fonts-liberation libnss3 libxss1 libgconf-2-4 libappindicator1 libindicator7 \
    libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdbus-1-3 \
    libgdk-pixbuf2.0-0 libnspr4 libxcomposite1 libxdamage1 libxrandr2 \
    xdg-utils libegl1 libglib2.0-0 ca-certificates gnupg2 lsb-release && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# -------------------------------
# 1. Install Google Chrome & ChromeDriver
# -------------------------------
RUN CHROME_VERSION="135.0.4163.0" && \
    wget -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt install -y /tmp/chrome.deb && rm /tmp/chrome.deb && \
    wget -O /tmp/chromedriver.zip https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROME_VERSION}/linux64/chromedriver-linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin && \
    mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver.zip /usr/local/bin/chromedriver-linux64

# -------------------------------
# 2. Install Microsoft Edge & EdgeDriver
# -------------------------------
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg && \
    install -o root -g root -m 644 microsoft.gpg /etc/apt/trusted.gpg.d/ && \
    sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge.list' && \
    apt-get update && apt-get install -y microsoft-edge-stable && \
    EDGE_VERSION=$(microsoft-edge --version | grep -oP '\d+\.\d+\.\d+\.\d+') && \
    wget -O /tmp/edgedriver.zip "https://msedgedriver.azureedge.net/${EDGE_VERSION}/edgedriver_linux64.zip" && \
    unzip /tmp/edgedriver.zip -d /usr/local/bin && \
    chmod +x /usr/local/bin/msedgedriver && \
    rm -rf /tmp/edgedriver.zip microsoft.gpg

# -------------------------------
# 3. Setup Python & Your App
# -------------------------------
WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt selenium

# Expose Flask port
EXPOSE 5000

CMD ["python", "api.py"]
