FROM python:3.10

# Install system dependencies + Chromium
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg lsb-release ca-certificates \
    chromium chromium-driver \
    libnss3 libxss1 libappindicator1 libatk-bridge2.0-0 libgtk-3-0 libxkbcommon0 libvulkan1 \
    libasound2 libatk1.0-0 libcups2 libdbus-1-3 libgdk-pixbuf2.0-0 libnspr4 libxcomposite1 libxdamage1 libxrandr2 \
    xdg-utils software-properties-common

# ===============================
# ✅ Edge + EdgeDriver (v122)
# ===============================
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft.gpg &>    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/edge stable>    apt-get update && apt-get install -y microsoft-edge-stable && \
    wget -O /tmp/edgedriver.zip https://msedgedriver.azureedge.net/135.0.3179.85/edgedriver_linux64.zip && \
    unzip /tmp/edgedriver.zip -d /usr/local/bin && \
    chmod +x /usr/local/bin/msedgedriver && \
    rm /tmp/edgedriver.zip

# Environment vars (Chromium)
ENV CHROME_BIN=/usr/bin/chromium
ENV PATH=$PATH:/usr/bin/chromedriver

# ===============================
# ✅ Backend App Setup
# ===============================
WORKDIR /app
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt selenium

# Expose Flask port
EXPOSE 5050

# Start Flask
CMD ["python", "api.py"]