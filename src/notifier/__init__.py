"""Notifier V2."""
import os

from src.notifier.telegram import send_telegram
from src.notifier.whatsapp_cloud import send_whatsapp_text as send_whatsapp_cloud_text


def notify(message):
    return send_telegram(message)


def send_whatsapp_text(to, text):
    provider = os.getenv("WHATSAPP_PROVIDER", "disabled").strip().lower()

    if provider == "disabled":
        return False

    if provider == "cloud":
        return send_whatsapp_cloud_text(to, text)

    return False
