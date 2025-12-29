FROM python:3.10
WORKDIR /app

# Install Chrome, xvfb, and dependencies for SeleniumBase
# xvfb provides a virtual display for TikTok scraping (TikTok blocks headless Chrome)
RUN apt-get update && apt-get install -y \
    wget gnupg unzip \
    xvfb \
    xauth \
    libxss1 \
    libappindicator3-1 \
    libasound2 \
    && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Playwright browsers (for fallback)
RUN playwright install chromium --with-deps

COPY . .
CMD ["python3", "run_all.py"]
