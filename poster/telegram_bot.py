import requests
import time
from config.telegram import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID


BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


# --------------------------------------------------
# ENVIO DE TEXTO
# --------------------------------------------------
def enviar_telegram(texto):
    url = f"{BASE_URL}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    try:
        response = requests.post(url, data=payload, timeout=10)

        if response.status_code != 200:
            print(f"⚠ Erro Telegram (texto): {response.text}")

    except Exception as e:
        print(f"🚨 Falha ao enviar texto Telegram: {e}")


# --------------------------------------------------
# ENVIO FOTO + TEXTO (COM LEGENDA)
# --------------------------------------------------
def enviar_telegram_foto_com_texto(texto, imagem_url):
    url = f"{BASE_URL}/sendPhoto"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": imagem_url,
        "caption": texto,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, data=payload, timeout=15)

        if response.status_code != 200:
            print(f"⚠ Erro Telegram (foto): {response.text}")

    except Exception as e:
        print(f"🚨 Falha ao enviar foto Telegram: {e}")


