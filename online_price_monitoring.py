import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

def fetch_price(url):
    """Функция для получения цены с указанного сайта."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        price = "Цена не найдена"
        
        # Пример парсинга (нужно уточнять для каждого сайта)
        if "off-mar.ru" in url:
            price_tag = soup.find("span", class_="price")
        elif "bumaga27.ru" in url:
            price_tag = soup.find("div", class_="product-price")
        elif "kanz27.ru" in url:
            price_tag = soup.find("span", class_="price-new")
        elif "klayd.ru" in url:
            price_tag = soup.find("div", class_="product-price")
        elif "lunsvet.com" in url:
            price_tag = soup.find("span", class_="price-value")
        else:
            price_tag = None
        
        if price_tag:
            price = price_tag.text.strip()
        
        return price
    except Exception as e:
        return f"Ошибка: {e}"

# Интерфейс Streamlit
st.title("Онлайн-мониторинг цен конкурентов")

# Ввод URL для мониторинга
url_input = st.text_input("Введите ссылку на товар конкурента")

if st.button("Проверить цену"):
    if url_input:
        price = fetch_price(url_input)
        st.write(f"Цена: {price}")
    else:
        st.warning("Введите ссылку!")

# Таблица для отображения данных
st.subheader("История цен")
data = {"Товар": ["Бумага Снегурочка А4", "Бумага SvetoCopy A4"],
        "Сайт": ["off-mar.ru", "bumaga27.ru", "kanz27.ru", "klayd.ru", "lunsvet.com"],
        "Цена, ₽": [fetch_price("https://off-mar.ru/product-category/kancelyarskie-tovary/bumaga-plenka/bumaga-ofisnaya/"), 
                     fetch_price("https://www.bumaga27.ru/catalog/bumaga/bumaga_dlya_kopiy_i_pechati/?display=list&order=asc&sort=PRICE"),
                     fetch_price("https://kanz27.ru/bumaga-dlya-ofisnoy-tekhniki/bumaga-formatnaya/"),
                     fetch_price("https://klayd.ru/catalog/ofisnaya-yevropapir/"),
                     fetch_price("https://lunsvet.com/catalog/kantselyariya/")],
        "Дата обновления": ["2025-01-30", "2025-01-30", "2025-01-30", "2025-01-30", "2025-01-30"]}
df = pd.DataFrame(data)
st.dataframe(df)
