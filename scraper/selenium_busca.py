import random
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


def iniciar_driver():
    options = Options()

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service("C:/chromedriver/chromedriver.exe")

    driver = webdriver.Chrome(service=service, options=options)

    return driver



def scroll_humano(driver):
    altura_total = driver.execute_script("return document.body.scrollHeight")

    for i in range(1, 5):
        driver.execute_script(
            f"window.scrollTo(0, {altura_total * i/5});"
        )
        time.sleep(random.uniform(1.2, 2.8))




def buscar_mercadolivre_selenium(driver,termo, limite=10):

    url = f"https://lista.mercadolivre.com.br/{termo.replace(' ', '-')}"
    driver.get(url)

    time.sleep(random.uniform(2, 4))
    scroll_humano(driver)


    time.sleep(random.uniform(2, 4))

    links = []

    items = driver.find_elements(By.XPATH, "//a[contains(@href, '/p/')]")

    print(f"Itens encontrados ML: {len(items)}")

    for item in items:
        link = item.get_attribute("href")

        if link and "/p/" in link:
            link_limpo = link.split("?")[0].split("#")[0]

            if link_limpo not in links:
                links.append(link_limpo)

        if len(links) >= limite:
            break
    
    return links
    



def buscar_amazon_selenium(driver, termo, limite=10):

    links = []

    try:
        url = f"https://www.amazon.com.br/s?k={termo.replace(' ', '+')}"
        driver.get(url)

        time.sleep(random.uniform(8, 15))
        scroll_humano(driver)
        time.sleep(random.uniform(4, 7))

        items = driver.find_elements(By.CSS_SELECTOR, "a.a-link-normal.s-no-outline")

        print(f"Itens encontrados Amazon: {len(items)}")

        for item in items:

            try:
                link = item.get_attribute("href")

                if link and "/dp/" in link:
                    link_limpo = link.split("?")[0]

                    if link_limpo not in links:
                        links.append(link_limpo)

                if len(links) >= limite:
                    break

            except Exception:
                continue

    except Exception as e:
        print("⚠ Erro interno Amazon:", e)

    return links

