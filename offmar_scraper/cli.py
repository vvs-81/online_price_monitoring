from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import List, Optional, Set, Deque
from collections import deque

import typer
from bs4 import BeautifulSoup
from tqdm import tqdm

from .http_client import HttpClient
from .parsers import parse_category_products, parse_pagination_urls, parse_product_page, parse_category_links
from .snapshot import SnapshotRow, write_snapshot, today_date_str
from .sales import compute_sales_for_date, write_sales_csv
from .sheets import append_rows, append_table_rows


app = typer.Typer(add_completion=False, no_args_is_help=True)


def _default_user_agent() -> str:
	return (
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
		"(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
	)


@app.command()
def scrape(
	category: str = typer.Option(..., help="Category URL to scrape"),
	outdir: Path = typer.Option(Path("data"), help="Output base directory"),
	user_agent: str = typer.Option(_default_user_agent(), help="HTTP User-Agent"),
	max_pages: Optional[int] = typer.Option(None, help="Limit number of pages to scrape"),
	sheets_spreadsheet: Optional[str] = typer.Option(None, help="Spreadsheet to append snapshot"),
	sheets_tab_snapshots: str = typer.Option("snapshots", help="Snapshots tab name"),
	sa_path: str = typer.Option("gcp_service_account.json", help="Service account JSON path"),
) -> None:
	client = HttpClient(user_agent=user_agent)
	visited_pages: List[str] = []
	to_visit: List[str] = [category]
	all_links = []
	# Discover all pages (simple breadth-first within pagination)
	while to_visit:
		page_url = to_visit.pop(0)
		if page_url in visited_pages:
			continue
		resp = client.get(page_url)
		soup = BeautifulSoup(resp.text, "lxml")
		visited_pages.append(page_url)
		all_links.extend(parse_category_products(soup))
		for p in parse_pagination_urls(soup):
			if p not in visited_pages and p not in to_visit:
				to_visit.append(p)
		if max_pages is not None and len(visited_pages) >= max_pages:
			break
	# Visit product pages
	rows: List[SnapshotRow] = []
	for link in tqdm(all_links, desc="Products"):
		try:
			resp = client.get(link.url)
			soup = BeautifulSoup(resp.text, "lxml")
			pd = parse_product_page(link.url, soup)
			# Fallbacks from category card for missing fields
			final_title = pd.title or (link.title or "")
			final_price = pd.price_text or link.price_text
			final_qty = pd.stock_quantity if pd.stock_quantity is not None else link.stock_quantity
			rows.append(
				SnapshotRow(
					snapshot_date=today_date_str(),
					product_url=pd.url,
					product_title=final_title,
					sku=pd.sku,
					price_text=final_price,
					regular_price_text=pd.regular_price_text,
					sale_price_text=pd.sale_price_text,
					currency=pd.currency,
					stock_status=pd.stock_status,
					stock_quantity=final_qty,
					category_path=pd.category_path,
				)
			)
		except Exception as e:
			print(f"Failed to parse {link.url}: {e}")
	csv_path = write_snapshot(outdir, rows)
	print(f"Wrote snapshot: {csv_path}")
	# Auto-export snapshot rows to Sheets if configured
	if sheets_spreadsheet:
		# Read CSV (including header) and append; ensure headers present in sheet
		import csv as _csv
		with csv_path.open("r", encoding="utf-8") as f:
			reader = list(_csv.reader(f))
		if reader:
			headers, data_rows = reader[0], reader[1:]
			append_table_rows(
				spreadsheet_name=sheets_spreadsheet,
				tab_name=sheets_tab_snapshots,
				rows=data_rows,
				sa_path=sa_path,
				headers=headers,
			)
			print(f"Appended snapshot ({len(data_rows)} rows) to Sheets tab '{sheets_tab_snapshots}'")


@app.command()
def compute_sales(
	snapshots: Path = typer.Option(Path("data/snapshots"), help="Snapshots directory"),
	date: Optional[str] = typer.Option(None, help="Date YYYY-MM-DD; defaults to today"),
	out: Optional[Path] = typer.Option(None, help="Output CSV path for computed sales"),
	sheets_spreadsheet: Optional[str] = typer.Option(None, help="Spreadsheet name to append"),
	sheets_tab_sales: str = typer.Option("sales", help="Tab name for sales"),
	sa_path: str = typer.Option("gcp_service_account.json", help="Service account JSON path"),
) -> None:
	date_str = date or today_date_str()
	rows = compute_sales_for_date(snapshots, date_str)
	if out is None:
		out = Path("data") / "sales" / f"{date_str}.csv"
	out_path = write_sales_csv(out, rows)
	print(f"Wrote sales: {out_path}")
	if sheets_spreadsheet:
		append_table_rows(
			spreadsheet_name=sheets_spreadsheet,
			tab_name=sheets_tab_sales,
			rows=[r.to_csv_row() for r in rows],
			sa_path=sa_path,
			headers=[
				"date","product_url","product_title","sku","units_sold","revenue_rub","price_used_text"
			],
		)
		print(f"Appended {len(rows)} sales rows to Sheets tab '{sheets_tab_sales}'")


@app.command()
def export_snapshot_to_sheets(
	date: Optional[str] = typer.Option(None, help="Date YYYY-MM-DD; defaults to today"),
	outdir: Path = typer.Option(Path("data"), help="Output base directory"),
	sheets_spreadsheet: str = typer.Option(..., help="Spreadsheet name to append"),
	sheets_tab_snapshots: str = typer.Option("snapshots", help="Tab name for snapshots"),
	sa_path: str = typer.Option("gcp_service_account.json", help="Service account JSON path"),
) -> None:
	date_str = date or today_date_str()
	csv_path = outdir / "snapshots" / f"{date_str}.csv"
	import csv
	with csv_path.open("r", encoding="utf-8") as f:
		reader = csv.reader(f)
		rows = list(reader)
	# skip header row: Sheets append_rows expects data rows only when mixing snapshots across days
	append_rows(
		spreadsheet_name=sheets_spreadsheet,
		tab_name=sheets_tab_snapshots,
		rows=rows,
		sa_path=sa_path,
	)
	print(f"Appended snapshot {date_str} ({len(rows)} rows) to Sheets tab '{sheets_tab_snapshots}'")


@app.command()
def run_daily(
	categories: List[str] = typer.Option(..., help="One or more category URLs"),
	outdir: Path = typer.Option(Path("data"), help="Output base directory"),
	user_agent: str = typer.Option(_default_user_agent(), help="HTTP User-Agent"),
	max_pages: Optional[int] = typer.Option(None, help="Limit pages per category"),
	sheets_spreadsheet: Optional[str] = typer.Option(None, help="Spreadsheet to export"),
	sheets_tab_sales: str = typer.Option("sales", help="Sales tab name"),
	sheets_tab_snapshots: str = typer.Option("snapshots", help="Snapshots tab name"),
	sa_path: str = typer.Option("gcp_service_account.json", help="Service account JSON path"),
) -> None:
	# Scrape all categories
	for cat in categories:
		print(f"Scraping category: {cat}")
		scrape.callback(category=cat, outdir=outdir, user_agent=user_agent, max_pages=max_pages)  # type: ignore
	# Compute sales
	date_str = today_date_str()
	rows = compute_sales_for_date(outdir / "snapshots", date_str)
	out_sales = Path("data") / "sales" / f"{date_str}.csv"
	write_sales_csv(out_sales, rows)
	print(f"Wrote sales: {out_sales}")
	# Export to Sheets if configured
	if sheets_spreadsheet:
		append_table_rows(
			spreadsheet_name=sheets_spreadsheet,
			tab_name=sheets_tab_sales,
			rows=[r.to_csv_row() for r in rows],
			sa_path=sa_path,
			headers=[
				"date","product_url","product_title","sku","units_sold","revenue_rub","price_used_text"
			],
		)
		print(f"Appended sales to Sheets tab '{sheets_tab_sales}'")
		# Also append snapshots
		csv_path = outdir / "snapshots" / f"{date_str}.csv"
		import csv
		with csv_path.open("r", encoding="utf-8") as f:
			reader = csv.reader(f)
			rows_csv = list(reader)
		if rows_csv:
			headers, data_rows = rows_csv[0], rows_csv[1:]
			append_table_rows(
				spreadsheet_name=sheets_spreadsheet,
				tab_name=sheets_tab_snapshots,
				rows=data_rows,
				sa_path=sa_path,
				headers=headers,
			)
		print(f"Appended snapshot to Sheets tab '{sheets_tab_snapshots}'")


@app.command()
def scrape_all(
	root: str = typer.Option("https://off-mar.ru/product-category/", help="Root category URL"),
	outdir: Path = typer.Option(Path("data"), help="Output base directory"),
	user_agent: str = typer.Option(_default_user_agent(), help="HTTP User-Agent"),
	max_pages_per_category: Optional[int] = typer.Option(None, help="Limit pages per category"),
	sheets_spreadsheet: Optional[str] = typer.Option(None, help="Spreadsheet to append snapshot"),
	sheets_tab_snapshots: str = typer.Option("snapshots", help="Snapshots tab name"),
	sa_path: str = typer.Option("gcp_service_account.json", help="Service account JSON path"),
) -> None:
	client = HttpClient(user_agent=user_agent)
	visited: Set[str] = set()
	queue: Deque[str] = deque([root])
	all_categories: List[str] = []
	# BFS over category links
	while queue:
		url = queue.popleft()
		if url in visited:
			continue
		try:
			resp = client.get(url)
			soup = BeautifulSoup(resp.text, "lxml")
			visited.add(url)
			# if page displays products, treat as category to scrape
			if soup.select("div.products"):  # heuristic: has product containers
				all_categories.append(url)
			# enqueue discovered category links
			for href in parse_category_links(soup):
				if href not in visited:
					queue.append(href)
		except Exception as e:
			print(f"Discovery failed for {url}: {e}")
	# De-duplicate, keep only URLs with /product-category/
	all_categories = [u for u in dict.fromkeys([u for u in all_categories if "/product-category/" in u])]
	print(f"Discovered categories: {len(all_categories)}")
	# Scrape each category
	for cat in all_categories:
		print(f"Scraping category: {cat}")
		scrape.callback(
			category=cat,
			outdir=outdir,
			user_agent=user_agent,
			max_pages=max_pages_per_category,
			sheets_spreadsheet=sheets_spreadsheet,
			sheets_tab_snapshots=sheets_tab_snapshots,
			sa_path=sa_path,
		)  # type: ignore


if __name__ == "__main__":
	app()