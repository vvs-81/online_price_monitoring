import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.parse

def fetch_product_info(url):
    """Получает название и цену товара с lunsvet.com"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        product_name = "Не найдено"
        price = "Цена не найдена"
        
        name_tag = soup.find("h1")  # Заголовок товара
        price_tag = soup.find("span", class_="price-value")
        
        if name_tag:
            product_name = name_tag.text.strip()
        if price_tag:
            price = float(price_tag.text.replace("₽", "").replace(" ", "").strip())
        
        return product_name, price
    except Exception as e:
        return "Ошибка", "Ошибка"

def fetch_competitor_prices(product_name):
    """Находит цены на товар на сайтах конкурентов."""
    encoded_name = urllib.parse.quote_plus(product_name)  # Кодируем для URL
    competitors = [
        ("off-mar.ru", f"https://off-mar.ru/search/?q={encoded_name}"),
        ("bumaga27.ru", f"https://www.bumaga27.ru/search/?q={encoded_name}"),
        ("kanz27.ru", f"https://kanz27.ru/catalog/?search={encoded_name}"),
        ("klayd.ru", f"https://klayd.ru/catalog/?search={encoded_name}")
    ]
    
    results = []
    for site, search_url in competitors:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Поиск первой найденной цены на странице
            price_tag = soup.find("span", class_="price") or soup.find("div", class_="product-price") or soup.find("span", class_="product-cost")
            
            if price_tag:
                price_text = price_tag.text.replace("₽", "").replace(" ", "").strip()
                try:
                    price = float(price_text)
                    results.append((site, price))
                except ValueError:
                    continue
        except:
            continue
    
    return results

# Интерфейс Streamlit
st.title("Автоматический мониторинг цен конкурентов")

# Ввод URL товара на вашем сайте
url_input = st.text_input("Введите ссылку на товар с вашего сайта")

if st.button("Анализировать цены"):
    if url_input:
        product_name, our_price = fetch_product_info(url_input)
        competitor_prices = fetch_competitor_prices(product_name)
        
        if competitor_prices:
            competitor_prices.sort(key=lambda x: x[1])  # Сортировка по цене
            lowest_price = competitor_prices[0][1]
            lowest_competitor = competitor_prices[0][0]
            price_difference = our_price - lowest_price
            
            # Вывод результатов
            st.write(f"**Название товара:** {product_name}")
            st.write(f"**Наша цена:** {our_price} ₽")
            st.write(f"**Минимальная цена у конкурента:** {lowest_price} ₽ ({lowest_competitor})")
            st.write(f"**Разница в цене:** {'+' if price_difference > 0 else ''}{price_difference} ₽")
            
            # Отображение всех цен конкурентов
            df = pd.DataFrame(competitor_prices, columns=["Конкурент", "Цена, ₽"])
            st.dataframe(df)
        else:
            st.warning("Не удалось найти цены у конкурентов. Проверьте, доступен ли товар на их сайтах.")
    else:
        st.warning("Введите ссылку!")
