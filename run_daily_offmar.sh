#!/usr/bin/env bash
set -euo pipefail

# Config
WORKDIR="/workspace"
VENV_PATH="$WORKDIR/.venv"
PY="$VENV_PATH/bin/python"
LOG="$WORKDIR/cron.log"
OUTDIR="$WORKDIR/data"
SPREADSHEET_NAME="Offmar Sales"
SA_PATH="$WORKDIR/gcp_service_account.json"
ROOT_CAT="https://off-mar.ru/product-category/"

# Ensure venv exists
if [ ! -x "$PY" ]; then
	echo "Python venv not found at $PY" >&2
	exit 1
fi

# Run: discover all categories, scrape, compute sales and export
cd "$WORKDIR"
"$PY" -m offmar_scraper.cli scrape_all \
	--root "$ROOT_CAT" \
	--outdir "$OUTDIR" \
	--sheets-spreadsheet "$SPREADSHEET_NAME" \
	--sheets-tab-snapshots "snapshots" \
	--sa-path "$SA_PATH"

# Compute and export sales for today
"$PY" -m offmar_scraper.cli compute-sales \
	--snapshots "$OUTDIR/snapshots" \
	--sheets-spreadsheet "$SPREADSHEET_NAME" \
	--sheets-tab-sales "sales" \
	--sa-path "$SA_PATH"