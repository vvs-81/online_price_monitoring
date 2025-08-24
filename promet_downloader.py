#!/usr/bin/env python3
"""
Promet XLS downloader

Logs into https://lk.promet.ru/Sklad/SkladV using credentials from env/CLI
and clicks the "Вывод склада в XLS" button to download the file.

Environment variables:
- PROMET_USERNAME: login/username
- PROMET_PASSWORD: password
- PROMET_HEADLESS: true/false (default: true)
- PROMET_DOWNLOAD_DIR: directory for downloads (default: ./downloads)

CLI overrides:
  python3 promet_downloader.py --username USER --password PASS [--headless true] [--download-dir /path]
"""
import argparse
import os
import sys
import time
from pathlib import Path
from typing import Iterable, Optional

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


BASE_URL = "https://lk.promet.ru"
TARGET_PATH = "/Sklad/SkladV"
EXPORT_BUTTON_TEXT = "Вывод склада в XLS"


def getenv_bool(name: str, default: bool) -> bool:
	val = os.getenv(name)
	if val is None:
		return default
	val_lower = val.strip().lower()
	return val_lower in {"1", "true", "yes", "y", "on"}


def try_fill(page, selectors: Iterable[str], value: str, timeout_ms: int = 2000) -> Optional[str]:
	for selector in selectors:
		try:
			locator = page.locator(selector).first
			if locator.count() == 0:
				continue
			locator.wait_for(state="visible", timeout=timeout_ms)
			locator.fill(value)
			return selector
		except Exception:
			continue
	return None


def try_click(page, selectors: Iterable[str], timeout_ms: int = 3000) -> Optional[str]:
	for selector in selectors:
		try:
			locator = page.locator(selector).first
			if locator.count() == 0:
				continue
			locator.wait_for(state="visible", timeout=timeout_ms)
			locator.click()
			return selector
		except Exception:
			continue
	return None


def perform_login(page, username: str, password: str) -> None:
	# Attempt to land on the target page; expect redirect to login if unauthenticated.
	page.goto(BASE_URL + TARGET_PATH, wait_until="domcontentloaded")

	# Candidate selectors for username and password fields (Russian + generic fallbacks)
	username_selectors = [
		'input[name="Login"]',
		'input[name="login"]',
		'input#Login',
		'input[name="Email"]',
		'input[name="email"]',
		'input[placeholder*="логин" i]',
		'input[placeholder*="e-mail" i]',
		'input[placeholder*="email" i]',
		'input[type="text"]',
	]
	password_selectors = [
		'input[name="Password"]',
		'input[name="password"]',
		'input#Password',
		'input[placeholder*="парол" i]',
		'input[type="password"]',
	]
	login_button_selectors = [
		'button:has-text("Войти")',
		'button[type="submit"]',
		'input[type="submit"]',
		'text=Войти',
		'button:has-text("Log in")',
	]

	filled_user = try_fill(page, username_selectors, username)
	filled_pass = try_fill(page, password_selectors, password)
	if not (filled_user and filled_pass):
		# If we didn't find fields immediately, wait briefly and retry once
		page.wait_for_timeout(1000)
		filled_user = filled_user or try_fill(page, username_selectors, username)
		filled_pass = filled_pass or try_fill(page, password_selectors, password)

	if not (filled_user and filled_pass):
		raise RuntimeError("Не удалось найти поля логина/пароля. Проверьте страницу входа.")

	clicked = try_click(page, login_button_selectors)
	if not clicked:
		# Press Enter in password field as a fallback
		page.keyboard.press("Enter")

	# Wait for navigation after login
	try:
		page.wait_for_load_state("networkidle", timeout=15000)
	except PlaywrightTimeoutError:
		# Continue; some pages are dynamic and may not go idle
		pass

	# Ensure we are on the target area
	page.goto(BASE_URL + TARGET_PATH, wait_until="domcontentloaded")


def click_export_and_download(page, download_dir: Path) -> Path:
	# Primary: role-based match for reliability
	export_selectors = [
		# Role-based queries are only available via get_by_role in sync API
		f'role=button[name="{EXPORT_BUTTON_TEXT}"]',
		f'role=link[name="{EXPORT_BUTTON_TEXT}"]',
		'button:has-text("Вывод склада в XLS")',
		'a:has-text("Вывод склада в XLS")',
		'text=Вывод склада в XLS',
		'a[href*="xls"]',
		'a[href*="XLS"]',
	]

	# Convert our pseudo role=... into actual locators where applicable
	locators = []
	for sel in export_selectors:
		if sel.startswith("role=button["):
			name = EXPORT_BUTTON_TEXT
			locators.append(lambda: page.get_by_role("button", name=name))
		elif sel.startswith("role=link["):
			name = EXPORT_BUTTON_TEXT
			locators.append(lambda: page.get_by_role("link", name=name))
		else:
			locators.append(lambda sel=sel: page.locator(sel).first)

	last_error: Optional[Exception] = None
	for make_locator in locators:
		try:
			locator = make_locator()
			if locator.count() == 0:
				continue
			locator.wait_for(state="visible", timeout=5000)
			with page.expect_download(timeout=60000) as download_info:
				locator.click()
			download = download_info.value
			suggested = download.suggested_filename or f"promet_sklad_{int(time.time())}.xls"
			target_path = download_dir / suggested
			download.save_as(str(target_path))
			return target_path
		except Exception as exc:
			last_error = exc
			continue

	raise RuntimeError(f"Не удалось найти кнопку выгрузки XLS. Последняя ошибка: {last_error}")


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Promet XLS downloader")
	parser.add_argument("--username", help="Login/username", default=os.getenv("PROMET_USERNAME"))
	parser.add_argument("--password", help="Password", default=os.getenv("PROMET_PASSWORD"))
	parser.add_argument("--headless", help="Run headless (true/false)", default=os.getenv("PROMET_HEADLESS", "true"))
	parser.add_argument("--download-dir", help="Download directory", default=os.getenv("PROMET_DOWNLOAD_DIR", "./downloads"))
	return parser.parse_args()


def run_download(username: str, password: str, headless: bool, download_dir: Path) -> Path:
	with sync_playwright() as p:
		browser = p.chromium.launch(headless=headless)
		context = browser.new_context(accept_downloads=True, locale="ru-RU")
		page = context.new_page()
		try:
			perform_login(page, username, password)
			file_path = click_export_and_download(page, Path(download_dir))
			return file_path
		finally:
			context.close()
			browser.close()


def main() -> int:
	load_dotenv()
	args = parse_args()

	username = args.username
	password = args.password
	if not username or not password:
		print("Ошибка: PROMET_USERNAME и PROMET_PASSWORD должны быть заданы (в .env или как флаги).", file=sys.stderr)
		return 2

	headless = str(args.headless).strip().lower() in {"1", "true", "yes", "y", "on"}
	download_dir = Path(args.download_dir).expanduser().resolve()
	download_dir.mkdir(parents=True, exist_ok=True)

	print(f"Логин в Promet и выгрузка XLS... (headless={headless})")
	file_path = run_download(username=username, password=password, headless=headless, download_dir=download_dir)
	print(f"Файл сохранен: {file_path}")
	return 0


if __name__ == "__main__":
	sys.exit(main())