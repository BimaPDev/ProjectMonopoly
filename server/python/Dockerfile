FROM python:3.10
WORKDIR /app

# Install Chrome and dependencies for undetected-chromedriver
RUN apt-get update && apt-get install -y wget gnupg unzip && \
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install  -r requirements.txt
COPY . .
CMD ["python3", "run_all.py"]
