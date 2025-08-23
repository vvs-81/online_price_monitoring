from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


@dataclass
class SalesRow:
	date: str
	product_url: str
	product_title: str
	sku: Optional[str]
	units_sold: Optional[int]
	revenue_rub: Optional[float]
	price_used_text: Optional[str]

	def to_csv_row(self) -> List[str]:
		return [
			self.date,
			self.product_url,
			self.product_title,
			self.sku or "",
			str(self.units_sold) if self.units_sold is not None else "",
			(f"{self.revenue_rub:.2f}") if self.revenue_rub is not None else "",
			self.price_used_text or "",
		]

	@staticmethod
	def headers() -> List[str]:
		return [
			"date",
			"product_url",
			"product_title",
			"sku",
			"units_sold",
			"revenue_rub",
			"price_used_text",
		]


def _read_snapshot(path: Path) -> pd.DataFrame:
	df = pd.read_csv(path)
	# normalize URL as key
	df["product_key"] = df["sku"].fillna("").astype(str)
	df.loc[df["product_key"] == "", "product_key"] = df["product_url"]
	return df


def compute_sales_for_date(snapshots_dir: Path, date: str) -> List[SalesRow]:
	cur_path = snapshots_dir / f"{date}.csv"
	if not cur_path.exists():
		raise FileNotFoundError(f"Snapshot for {date} not found: {cur_path}")
	# find previous snapshot
	all_files = sorted([p for p in snapshots_dir.glob("*.csv")])
	prev_path: Optional[Path] = None
	for p in all_files:
		if p.name < cur_path.name:
			prev_path = p
		else:
			break
	if prev_path is None:
		return []
	prev_df = _read_snapshot(prev_path)
	cur_df = _read_snapshot(cur_path)
	merged = cur_df.merge(
		prev_df[["product_key", "stock_quantity", "price_text", "product_title", "sku"]],
		left_on="product_key",
		right_on="product_key",
		suffixes=("", "_prev"),
		how="left",
	)
	rows: List[SalesRow] = []
	for _, r in merged.iterrows():
		prev_qty = r.get("stock_quantity_prev")
		cur_qty = r.get("stock_quantity")
		units_sold: Optional[int] = None
		if pd.notna(prev_qty) and pd.notna(cur_qty):
			try:
				units = int(prev_qty) - int(cur_qty)
				if units >= 0:
					units_sold = units
				# if units increased (restock), we don't count negative sales
			except Exception:
				units_sold = None
		# revenue
		revenue_rub: Optional[float] = None
		price_used_text: Optional[str] = None
		if units_sold is not None and units_sold > 0:
			price_used_text = r.get("price_text_prev") or r.get("price_text")
			if isinstance(price_used_text, str):
				price_num = _extract_price_number(price_used_text)
				if price_num is not None:
					revenue_rub = price_num * units_sold
		rows.append(
			SalesRow(
				date=date,
				product_url=r.get("product_url"),
				product_title=r.get("product_title"),
				sku=r.get("sku"),
				units_sold=units_sold,
				revenue_rub=revenue_rub,
				price_used_text=price_used_text,
			)
		)
	return rows


def _extract_price_number(price_text: str) -> Optional[float]:
	import re
	m = re.search(r"([\d\s]+[\,\.]?\d*)", price_text)
	if not m:
		return None
	num = m.group(1).replace(" ", "").replace(",", ".")
	try:
		return float(num)
	except Exception:
		return None


def write_sales_csv(out_path: Path, rows: List[SalesRow]) -> Path:
	out_path.parent.mkdir(parents=True, exist_ok=True)
	with out_path.open("w", newline="", encoding="utf-8") as f:
		writer = csv.writer(f)
		writer.writerow(SalesRow.headers())
		for r in rows:
			writer.writerow(r.to_csv_row())
	return out_path