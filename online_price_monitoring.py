import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

def fetch_price_and_name(url):
    """Получает название и цену товара по ссылке."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        product_name = "Не найдено"
        price = "Цена не найдена"
        
        name_tag = soup.find("h1")  # Заголовок товара
        price_tag = soup.find("span", class_="price") or soup.find("div", class_="product-price") or soup.find("span", class_="product-cost")
        
        if name_tag:
            product_name = name_tag.text.strip()
        if price_tag:
            try:
                price = float(price_tag.text.replace("₽", "").replace(" ", "").strip())
            except ValueError:
                price = "Цена не найдена"
        
        return product_name, price
    except Exception as e:
        return "Ошибка", "Ошибка"

# Интерфейс Streamlit
st.title("Автоматический мониторинг цен конкурентов")

# Ввод ссылок на товары конкурентов
competitor_urls = st.text_area("Введите ссылки на товары конкурентов (по одной в строке)").split("\n")

if st.button("Анализировать цены"):
    if competitor_urls:
        results = []
        for url in competitor_urls:
            url = url.strip()
            if url:
                product_name, price = fetch_price_and_name(url)
                results.append((url, product_name, price))
        
        # Создание DataFrame и отображение результатов
        df = pd.DataFrame(results, columns=["Ссылка", "Название товара", "Цена, ₽"])
        st.dataframe(df)
    else:
        st.warning("Введите хотя бы одну ссылку на товар конкурента!")
