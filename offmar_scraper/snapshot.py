from __future__ import annotations

import csv
import datetime as dt
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

import pytz


@dataclass
class SnapshotRow:
	snapshot_date: str
	product_url: str
	product_title: str
	sku: Optional[str]
	price_text: Optional[str]
	regular_price_text: Optional[str]
	sale_price_text: Optional[str]
	currency: Optional[str]
	stock_status: Optional[str]
	stock_quantity: Optional[int]
	category_path: Optional[str]

	def to_csv_row(self) -> List[str]:
		return [
			self.snapshot_date,
			self.product_url,
			self.product_title,
			self.sku or "",
			self.price_text or "",
			self.regular_price_text or "",
			self.sale_price_text or "",
			self.currency or "",
			self.stock_status or "",
			str(self.stock_quantity) if self.stock_quantity is not None else "",
			self.category_path or "",
		]

	@staticmethod
	def headers() -> List[str]:
		return [
			"snapshot_date",
			"product_url",
			"product_title",
			"sku",
			"price_text",
			"regular_price_text",
			"sale_price_text",
			"currency",
			"stock_status",
			"stock_quantity",
			"category_path",
		]


def ensure_dir(path: Path) -> None:
	path.mkdir(parents=True, exist_ok=True)


def today_date_str(tz: str = "Europe/Moscow") -> str:
	now = dt.datetime.now(pytz.timezone(tz))
	return now.strftime("%Y-%m-%d")


def snapshot_path(base_dir: Path, date_str: str) -> Path:
	return base_dir / "snapshots" / f"{date_str}.csv"


def write_snapshot(base_dir: Path, rows: List[SnapshotRow], date_str: Optional[str] = None) -> Path:
	date = date_str or today_date_str()
	csv_path = snapshot_path(base_dir, date)
	ensure_dir(csv_path.parent)
	new_file = not csv_path.exists()
	with csv_path.open("w", newline="", encoding="utf-8") as f:
		writer = csv.writer(f)
		writer.writerow(SnapshotRow.headers())
		for r in rows:
			writer.writerow(r.to_csv_row())
	return csv_path