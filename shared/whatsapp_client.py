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


def send_to_volunteers_group(signup_id, message: str) -> bool:
    """Ask the incident-management bot to post `message` to the volunteers
    WhatsApp group ("חמ - מתנדבים"). Whatsable can't address a group by name;
    the bot can, so we hand it the text and it sends it as-is.

    `signup_id` is the bot's dedupe key: re-sending the same id never posts
    twice, so a retry after a lost response is safe.

    Returns True if the message reached the group now, False if the bot saved
    it and will send it once its WhatsApp connection is back. Raises on any
    HTTP error (bad secret, bad body, bot down)."""
    base_url = (os.getenv("AGENT_BASE_URL") or "").rstrip("/")
    secret   = os.getenv("AGENT_API_SECRET")

    response = requests.post(
        f"{base_url}/api/volunteer-signup",
        headers={"Authorization": f"Bearer {secret}", "Content-Type": "application/json"},
        json={
            "event": "volunteer.signup",
            "incident_id": str(signup_id),
            "report_text": message,
        },
        timeout=_TIMEOUT,
    )
    if not response.ok:
        raise RuntimeError(f"Incident bot HTTP {response.status_code}")
    return bool(response.json().get("sent"))
