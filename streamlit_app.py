import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Promet XLS Downloader", page_icon="📦", layout="centered")
st.title("Скачивание склада Promet в XLS")

default_username = os.getenv("PROMET_USERNAME", "")
default_password = os.getenv("PROMET_PASSWORD", "")
default_headless = os.getenv("PROMET_HEADLESS", "true").strip().lower() in {"1","true","yes","y","on"}
default_download_dir = os.getenv("PROMET_DOWNLOAD_DIR", "/workspace/downloads")

with st.form("download_form"):
	username = st.text_input("Логин", value=default_username)
	password = st.text_input("Пароль", type="password", value=default_password)
	headless = st.checkbox("Фоновый режим (headless)", value=default_headless)
	download_dir = st.text_input("Папка для скачивания", value=default_download_dir)
	submitted = st.form_submit_button("Скачать XLS")

if submitted:
	if not username or not password:
		st.error("Введите логин и пароль.")
	else:
		from promet_downloader import run_download
		try:
			Path(download_dir).mkdir(parents=True, exist_ok=True)
			with st.spinner("Выполняется вход и скачивание файла..."):
				file_path = run_download(username=username, password=password, headless=headless, download_dir=Path(download_dir))
			st.success(f"Готово. Файл сохранен: {file_path}")
			try:
				data = Path(file_path).read_bytes()
				st.download_button(
					label="Скачать файл",
					data=data,
					file_name=Path(file_path).name,
					mime="application/vnd.ms-excel",
				)
			except Exception:
				pass
		except Exception as e:
			st.error(f"Ошибка: {e}")