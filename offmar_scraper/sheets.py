from __future__ import annotations

from typing import List, Optional

import gspread
from google.oauth2.service_account import Credentials


SCOPES = [
	"https://www.googleapis.com/auth/spreadsheets",
	"https://www.googleapis.com/auth/drive",
]


def _client_from_service_account(sa_path: str) -> gspread.Client:
	creds = Credentials.from_service_account_file(sa_path, scopes=SCOPES)
	return gspread.authorize(creds)


def ensure_worksheet(
	spreadsheet_name: str,
	tab_name: str,
	sa_path: str = "gcp_service_account.json",
	headers: Optional[List[str]] = None,
) -> gspread.Worksheet:
	gc = _client_from_service_account(sa_path)
	sh = gc.open(spreadsheet_name)
	try:
		ws = sh.worksheet(tab_name)
	except gspread.exceptions.WorksheetNotFound:
		ws = sh.add_worksheet(title=tab_name, rows="200", cols="26")
		if headers:
			ws.update("A1", [headers])
			return ws
	# If exists and header requested but empty, write headers once
	if headers:
		try:
			first_row = ws.row_values(1)
		except Exception:
			first_row = []
		if not first_row and headers:
			ws.update("A1", [headers])
	return ws


def append_table_rows(
	spreadsheet_name: str,
	tab_name: str,
	rows: List[List[str]],
	sa_path: str = "gcp_service_account.json",
	headers: Optional[List[str]] = None,
) -> None:
	ws = ensure_worksheet(spreadsheet_name, tab_name, sa_path=sa_path, headers=headers)
	if rows:
		ws.append_rows(rows, value_input_option="RAW")


def append_rows(
	spreadsheet_name: str,
	tab_name: str,
	rows: List[List[str]],
	sa_path: str = "gcp_service_account.json",
) -> None:
	# Backwards-compatible simple append (no header management)
	gc = _client_from_service_account(sa_path)
	sh = gc.open(spreadsheet_name)
	try:
		ws = sh.worksheet(tab_name)
	except gspread.exceptions.WorksheetNotFound:
		ws = sh.add_worksheet(title=tab_name, rows="100", cols="26")
	if rows:
		ws.append_rows(rows, value_input_option="RAW")