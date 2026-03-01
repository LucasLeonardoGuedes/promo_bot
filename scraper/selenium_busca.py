import random
import time
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ==========================================================
# DELAY HUMANO REALISTA
# ==========================================================

def delay_humano(minimo=1.2, maximo=3.8):
    """
    Delay não linear para parecer humano.
    """
    base = random.uniform(minimo, maximo)
    micro_pausa = random.uniform(0.1, 0.6)
    time.sleep(base + micro_pausa)


# ==========================================================
# SIMULA MOVIMENTO DE MOUSE
# ==========================================================

def movimento_mouse_humano(driver):
    try:
        actions = ActionChains(driver)
        largura = driver.execute_script("return window.innerWidth")
        altura = driver.execute_script("return window.innerHeight")

        for _ in range(random.randint(2, 5)):
            x = random.randint(50, largura - 50)
            y = random.randint(50, altura - 50)

            actions.move_by_offset(
                random.randint(-30, 30),
                random.randint(-30, 30)
            ).perform()

            time.sleep(random.uniform(0.2, 0.6))

    except:
        pass


# ==========================================================
# SCROLL HUMANO MELHORADO
# ==========================================================

def scroll_humano(driver):
    altura_total = driver.execute_script("return document.body.scrollHeight")
    passos = random.randint(4, 7)

    for i in range(1, passos + 1):
        driver.execute_script(
            f"window.scrollTo(0, {altura_total * i / passos});"
        )
        time.sleep(random.uniform(0.8, 2.3))


# ==========================================================
# DRIVER STEALTH MELHORADO
# ==========================================================





def iniciar_driver():
    options = webdriver.ChromeOptions()

    # BOA PRÁTICA: profile isolado (resolve MUITO o DevToolsActivePort)
    temp_profile = tempfile.mkdtemp(prefix="chrome_profile_")
    options.add_argument(f"--user-data-dir={temp_profile}")

    # estabilidade
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-features=Translate,NetworkService,NetworkServiceInProcess")

    # se você usa headless, prefira esse:
    # options.add_argument("--headless=new")

    # (opcional) força uma porta de debug
    options.add_argument("--remote-debugging-port=0")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    return driver

def iniciar_driver_whatsapp():

    options = Options()

    # Perfil exclusivo WhatsApp
    
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-data-dir=C:/chrome_whatsapp_profile")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    return driver


# ==========================================================
# BUSCAR AMAZON (STEALTH)
# ==========================================================

def buscar_amazon_selenium(driver, termo, limite=10):

    links = []

    try:
        url = f"https://www.amazon.com.br/s?k={termo.replace(' ', '+')}"
        driver.get(url)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        delay_humano(3, 6)
        movimento_mouse_humano(driver)
        scroll_humano(driver)

        if "captcha" in driver.page_source.lower():
            print("⚠ Amazon solicitando captcha")
            return []

        items = driver.find_elements(
            By.CSS_SELECTOR,
            "a.a-link-normal.s-no-outline"
        )

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

            except:
                continue

    except Exception as e:
        print("⚠ Erro interno Amazon:", e)

    return links


# ==========================================================
# BUSCAR MERCADO LIVRE (STEALTH)
# ==========================================================

def buscar_mercadolivre_selenium(driver, termo, limite=10):

    links = []

    try:
        url = f"https://lista.mercadolivre.com.br/{termo.replace(' ', '-')}"
        driver.get(url)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        delay_humano(2, 4)
        movimento_mouse_humano(driver)
        scroll_humano(driver)

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

    except Exception as e:
        print("⚠ Erro Mercado Livre:", e)

    return links