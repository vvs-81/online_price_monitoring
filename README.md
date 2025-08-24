Promet XLS Downloader

Requirements:
- Python 3.9+

Setup:
1. Copy env template and fill credentials:
   cp .env.example .env
   # Edit .env and set PROMET_USERNAME and PROMET_PASSWORD

2. Install Python packages and Playwright browser:
   python3 -m pip install --upgrade pip setuptools wheel
   python3 -m pip install -r requirements.txt
   python3 -m playwright install chromium

Run:
- Headless (default):
  python3 promet_downloader.py

- With flags or visible browser:
  python3 promet_downloader.py --username YOUR_LOGIN --password YOUR_PASS --headless false --download-dir /workspace/downloads

The downloaded XLS will be saved under the specified download directory.