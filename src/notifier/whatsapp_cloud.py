import logging
import os

try:
    import requests
except ImportError:
    requests = None


logger = logging.getLogger("v2.whatsapp_cloud")


def send_whatsapp_text(to, text):
    if requests is None:
        logger.warning("WhatsApp Cloud desativado: dependency requests não instalada")
        return False

    token = os.getenv("WHATSAPP_TOKEN", "").strip()
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    to = (to or "").strip()

    if not token or not phone_number_id or not to:
        logger.warning(
            "WhatsApp Cloud sem configuração completa (token=%s, phone_number_id=%s, to=%s)",
            bool(token),
            bool(phone_number_id),
            bool(to),
        )
        return False

    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code >= 400:
            logger.warning("WhatsApp Cloud HTTP %s body=%s", resp.status_code, resp.text)
            return False
        return True
    except requests.RequestException as exc:
        logger.warning("WhatsApp Cloud exception: %s", exc)
        return False

