import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def fetch_price_and_name(url):
    """Получает название и цену товара по ссылке через Selenium."""
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.get(url)
        time.sleep(3)  # Ждем загрузку страницы
        
        product_name = "Не найдено"
        price = "Цена не найдена"
        
        try:
            product_name = driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            pass
        
        try:
            if "lunsvet.com" in url:
                price = driver.find_element(By.CLASS_NAME, "price-value").text.strip()
            elif "off-mar.ru" in url:
                price = driver.find_element(By.CLASS_NAME, "price").text.strip()
            elif "bumaga27.ru" in url:
                price = driver.find_element(By.CLASS_NAME, "price").text.strip()
            elif "kanz27.ru" in url:
                price = driver.find_element(By.CLASS_NAME, "price").text.strip()
            elif "klayd.ru" in url:
                price = driver.find_element(By.CLASS_NAME, "price").text.strip()
            
            price = float(price.replace("₽", "").replace(" ", "").strip())
        except:
            price = "Цена не найдена"
        
        driver.quit()
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
