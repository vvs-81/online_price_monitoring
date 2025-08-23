# Offmar Daily Sales Scraper

This tool scrapes `off-mar.ru` product categories daily, stores snapshots (price, stock), computes day-over-day sales (units and revenue), and exports to Google Sheets.

## Features
- Category scraping with pagination
- Product detail parsing (name, SKU, price, stock status/quantity)
- Daily CSV snapshots per date
- Day-over-day sales computation
- Optional export to Google Sheets (service account)
- CLI for cron-friendly runs

## Setup
1. Python 3.10+
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. (Optional) Google Sheets service account:
   - Create a service account in Google Cloud and download JSON key.
   - Save file as `gcp_service_account.json` in project root or set `GOOGLE_APPLICATION_CREDENTIALS` env var.
   - Share the target spreadsheet with the service account email.

## Usage
Scrape a category and store snapshot:
```bash
python -m offmar_scraper.cli scrape \
  --category https://off-mar.ru/product-category/kancelyarskie-tovary/ofisnye-prinadlezhnosti/dyrokoly/ \
  --outdir data \
  --user-agent "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
```

Compute sales vs previous day and export to Sheets:
```bash
python -m offmar_scraper.cli compute-sales \
  --snapshots data/snapshots \
  --date YYYY-MM-DD \
  --sheets-spreadsheet "Offmar Sales" \
  --sheets-tab-sales "sales" \
  --sheets-tab-snapshots "snapshots"
```

End-to-end daily run (scrape, compute, export):
```bash
python -m offmar_scraper.cli run-daily \
  --categories https://off-mar.ru/product-category/kancelyarskie-tovary/ofisnye-prinadlezhnosti/dyrokoly/ \
  --outdir data \
  --sheets-spreadsheet "Offmar Sales" \
  --sheets-tab-sales "sales" \
  --sheets-tab-snapshots "snapshots"
```

## Cron Example
Run every day at 22:00 local time:
```cron
0 22 * * * cd /workspace && /usr/bin/python -m offmar_scraper.cli run-daily \
  --categories https://off-mar.ru/product-category/kancelyarskie-tovary/ofisnye-prinadlezhnosti/dyrokoly/ \
  --outdir /workspace/data \
  --sheets-spreadsheet "Offmar Sales" \
  --sheets-tab-sales "sales" \
  --sheets-tab-snapshots "snapshots" >> /workspace/cron.log 2>&1
```

## Notes
- Be respectful: throttle requests and cache where possible.
- Sales in units are inferred from daily stock quantity decreases. If the site does not expose stock quantities, unit sales cannot be computed reliably; revenue is approximated by count of out-of-stock transitions times last price.