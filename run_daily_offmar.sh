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
# Categories (space-separated if multiple)
CATEGORIES=(
	"https://off-mar.ru/product-category/kancelyarskie-tovary/ofisnye-prinadlezhnosti/dyrokoly/"
)

# Ensure venv exists
if [ ! -x "$PY" ]; then
	echo "Python venv not found at $PY" >&2
	exit 1
fi

# Run
cd "$WORKDIR"
"$PY" -m offmar_scraper.cli run-daily \
	--categories "${CATEGORIES[@]}" \
	--outdir "$OUTDIR" \
	--sheets-spreadsheet "$SPREADSHEET_NAME" \
	--sheets-tab-sales "sales" \
	--sheets-tab-snapshots "snapshots" \
	--sa-path "$SA_PATH"