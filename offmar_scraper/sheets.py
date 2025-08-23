from __future__ import annotations

from typing import List

import gspread
from google.oauth2.service_account import Credentials


SCOPES = [
	"https://www.googleapis.com/auth/spreadsheets",
	"https://www.googleapis.com/auth/drive",
]


def _client_from_service_account(sa_path: str) -> gspread.Client:
	creds = Credentials.from_service_account_file(sa_path, scopes=SCOPES)
	return gspread.authorize(creds)


def append_rows(
	spreadsheet_name: str,
	tab_name: str,
	rows: List[List[str]],
	sa_path: str = "gcp_service_account.json",
) -> None:
	gc = _client_from_service_account(sa_path)
	sh = gc.open(spreadsheet_name)
	try:
		ws = sh.worksheet(tab_name)
	except gspread.exceptions.WorksheetNotFound:
		ws = sh.add_worksheet(title=tab_name, rows="100", cols="26")
	if rows:
		ws.append_rows(rows, value_input_option="RAW")