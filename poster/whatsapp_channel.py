from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import os


# ======================================================
# PREPARAR CANAL
# ======================================================

def preparar_whatsapp_canal(driver, nome_canal):

    driver.get("https://web.whatsapp.com")
    print("🔐 Aguardando carregamento do WhatsApp...")

    wait = WebDriverWait(driver, 120)

    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//button[@aria-label='Canais']")
        )
    )

    driver.find_element(
        By.XPATH,
        "//button[@aria-label='Canais']"
    ).click()

    caixa = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//div[@aria-label='Caixa de texto de pesquisa']")
        )
    )

    driver.execute_script("arguments[0].click();", caixa)
    caixa.send_keys(nome_canal)

    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, f"//span[@title='{nome_canal}']")
        )
    )

    driver.find_element(
        By.XPATH,
        f"//span[@title='{nome_canal}']"
    ).click()

    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//footer//div[@contenteditable='true' and @role='textbox']")
        )
    )

    print("✅ Canal pronto para envio.")


# ======================================================
# ENVIAR TEXTO
# ======================================================



def remover_caracteres_nao_bmp(texto):
    return ''.join(c for c in texto if ord(c) <= 0xFFFF)

def enviar_mensagem_canal(driver, mensagem):

    wait = WebDriverWait(driver, 30)

    campo = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//footer//div[@contenteditable='true' and @role='textbox']")
        )
    )

    mensagem = remover_caracteres_nao_bmp(mensagem)

    driver.execute_script("""
        const campo = arguments[0];
        const texto = arguments[1];

        campo.innerHTML = texto.replace(/\\n/g, "<br>");
        campo.dispatchEvent(new Event('input', { bubbles: true }));
    """, campo, mensagem)

    time.sleep(1)

    campo.send_keys(Keys.ENTER)

    print("📤 Mensagem enviada via JS.")
# ======================================================
# ENVIAR IMAGEM + LEGENDA
# ======================================================

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import os
import time


from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import os
import time


def enviar_imagem_canal(driver, mensagem, url_imagem):

    try:
        mensagem = remover_caracteres_nao_bmp(mensagem)

        wait = WebDriverWait(driver, 40)

        caminho = "temp_imagem.jpg"

        # 1️⃣ Baixar imagem
        response = requests.get(url_imagem, stream=True)
        with open(caminho, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        # 2️⃣ Clicar botão +
        botao_anexo = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[@data-icon='plus']/ancestor::button")
            )
        )
        driver.execute_script("arguments[0].click();", botao_anexo)

        # 3️⃣ Upload
        input_file = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@type='file']")
            )
        )

        input_file.send_keys(os.path.abspath(caminho))

        # 4️⃣ Esperar preview abrir (MUITO IMPORTANTE)
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@role='dialog']")
            )
        )

        # 5️⃣ Campo legenda
        campo_legenda = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@role='textbox']")
            )
        )

        driver.execute_script("""
            const campo = arguments[0];
            const texto = arguments[1];
            campo.innerHTML = texto.replace(/\\n/g, "<br>");
            campo.dispatchEvent(new Event('input', { bubbles: true }));
        """, campo_legenda, mensagem)

        time.sleep(1)

        # 6️⃣ Botão enviar (mais robusto)
        botao_enviar = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[.//span[@data-icon='wds-ic-send-filled']]")
            )
        )

        driver.execute_script("arguments[0].click();", botao_enviar)

        print("📸 Imagem enviada com sucesso.")

        os.remove(caminho)

        return True

    except Exception as e:
        print("Erro interno enviar_imagem_canal:", e)
        return False