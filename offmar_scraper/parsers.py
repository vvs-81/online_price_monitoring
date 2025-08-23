from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from bs4 import BeautifulSoup, Tag


@dataclass
class CategoryProductLink:
	url: str
	title: Optional[str]
	price_text: Optional[str]
	stock_quantity: Optional[int] = None


@dataclass
class ProductDetails:
	url: str
	title: str
	sku: Optional[str]
	price_text: Optional[str]
	regular_price_text: Optional[str]
	sale_price_text: Optional[str]
	currency: Optional[str]
	stock_status: Optional[str]
	stock_quantity: Optional[int]
	category_path: Optional[str]


def _text_or_none(node: Optional[Tag]) -> Optional[str]:
	if not node:
		return None
	text = node.get_text(strip=True)
	return text or None


def parse_pagination_urls(soup: BeautifulSoup) -> List[str]:
	urls: List[str] = []
	nav = soup.select_one("nav.woocommerce-pagination, .pagination, nav.pagination")
	if not nav:
		return urls
	for a in nav.select("a.page-numbers, a.page, a"):
		href = a.get("href")
		if href and href not in urls:
			urls.append(href)
	return urls


def parse_category_products(soup: BeautifulSoup) -> List[CategoryProductLink]:
	results: List[CategoryProductLink] = []
	# Prefer the main loop grid to avoid sidebar/shortcode blocks
	grids = soup.select("div.products.wd-products[data-source='main_loop'], div.products[data-source='main_loop']")
	containers = grids if grids else soup.select("div.products")
	for container in containers:
		for card in container.select(".product, .wd-product"):
			classes = card.get("class", [])
			if any("product-category" == cls or cls.startswith("product-category") for cls in classes):
				continue
			# URL: prefer image link, fallback to title link, then any product link
			a = card.select_one("a.product-image-link") or card.select_one("h3.wd-entities-title a") or card.select_one("a[href*='/product/']")
			if not a:
				continue
			url = a.get("href")
			title = _text_or_none(card.select_one("h3.wd-entities-title, h2.woocommerce-loop-product__title, .product-title, h3"))
			price_text = _text_or_none(card.select_one("span.price, .price .amount, .woocommerce-Price-amount"))
			# Stock quantity on category card: span.av-qty
			stock_quantity: Optional[int] = None
			qty_text = _text_or_none(card.select_one("span.av-qty"))
			if qty_text:
				m = re.search(r"(\d+)", qty_text)
				if m:
					stock_quantity = int(m.group(1))
			if url:
				results.append(CategoryProductLink(url=url, title=title, price_text=price_text, stock_quantity=stock_quantity))
	return results


def _extract_price_parts(price_text: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
	if not price_text:
		return None, None
	m = re.search(r"([\d\s]+[\,\.]?\d*)", price_text)
	currency = None
	if "₽" in price_text or "руб" in price_text.lower():
		currency = "RUB"
	return (m.group(1).replace(" ", "") if m else None), currency


def parse_product_page(url: str, soup: BeautifulSoup) -> ProductDetails:
	title = _text_or_none(soup.select_one("h1.product_title, h1.entry-title, h1")) or ""
	sku = _text_or_none(soup.select_one("span.sku, .product_meta span.sku"))
	# Scope to product summary to avoid header/footer prices
	summary = soup.select_one("div.product .summary, .product .summary, .summary.entry-summary")
	regular_price_text = None
	sale_price_text = None
	price_text = None
	if summary:
		regular_price_text = _text_or_none(summary.select_one("p.price del .amount, del .woocommerce-Price-amount, del .amount"))
		sale_price_text = _text_or_none(summary.select_one("p.price ins .amount, ins .woocommerce-Price-amount, ins .amount"))
		price_text = _text_or_none(summary.select_one("p.price .amount, span.price .amount, .price .woocommerce-Price-amount"))
	if price_text is None:
		# conservative fallback: still try within product container
		product_container = soup.select_one("div.product")
		if product_container and not price_text:
			price_text = _text_or_none(product_container.select_one(".price .amount, .price .woocommerce-Price-amount"))
	# currency
	_, currency = _extract_price_parts(price_text or regular_price_text or sale_price_text)
	# stock
	stock_el = None
	if summary:
		stock_el = summary.select_one(".stock, .info-instock, p.stock")
	if stock_el is None:
		stock_el = soup.select_one("div.product .stock, div.product p.stock")
	stock_status = None
	stock_quantity: Optional[int] = None
	if stock_el:
		stock_text = stock_el.get_text(strip=True)
		lower = stock_text.lower()
		stock_status = "in_stock" if ("в наличии" in lower or "instock" in stock_el.get("class", [])) else ("out_of_stock" if "нет в наличии" in lower else stock_text)
		m = re.search(r"(\d+)", stock_text)
		if m:
			stock_quantity = int(m.group(1))
	# breadcrumb path
	crumbs = [
		li.get_text(strip=True)
		for li in soup.select("nav.woocommerce-breadcrumb a, .breadcrumbs a")
	]
	category_path = " > ".join(crumbs) if crumbs else None
	return ProductDetails(
		url=url,
		title=title,
		sku=sku,
		price_text=price_text,
		regular_price_text=regular_price_text,
		sale_price_text=sale_price_text,
		currency=currency,
		stock_status=stock_status,
		stock_quantity=stock_quantity,
		category_path=category_path,
	)