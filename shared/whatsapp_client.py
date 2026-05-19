import os
import requests

_TIMEOUT = 30


def send_whatsapp_message(message: str):
    api_key = os.getenv("WHATSABLE_API_KEY")
    phone   = os.getenv("PHONE_NUMBER")

    response = requests.post(
        "https://dashboard.whatsable.app/api/whatsapp/messages/v2.0.0/send",
        headers={"Authorization": api_key, "Content-Type": "application/json"},
        json={"to": phone, "text": message},
        timeout=_TIMEOUT,
    )
    if not response.ok:
        raise RuntimeError(f"Whatsable API HTTP {response.status_code}")
