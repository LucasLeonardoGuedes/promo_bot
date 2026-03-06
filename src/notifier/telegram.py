import os

try:
    import requests
except ImportError:
    requests = None


def send_telegram(text, photo_path=None):
    if requests is None:
        return {"sent": False, "reason": "requests dependency not installed"}

    token = os.getenv("TELEGRAM_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        return {"sent": False, "reason": "missing TELEGRAM_TOKEN/TELEGRAM_CHAT_ID"}

    base_url = f"https://api.telegram.org/bot{token}"

    try:
        if photo_path:
            url = f"{base_url}/sendPhoto"
            with open(photo_path, "rb") as photo_file:
                response = requests.post(
                    url,
                    data={
                        "chat_id": chat_id,
                        "caption": text,
                        "parse_mode": "HTML",
                    },
                    files={"photo": photo_file},
                    timeout=20,
                )
        else:
            url = f"{base_url}/sendMessage"
            response = requests.post(
                url,
                data={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                },
                timeout=15,
            )

        if response.status_code != 200:
            return {"sent": False, "reason": f"telegram http {response.status_code}: {response.text}"}

        return {"sent": True, "reason": "ok"}
    except Exception as exc:
        return {"sent": False, "reason": f"telegram exception: {exc}"}
