import os
import requests

_TIMEOUT = 30


def send_email(to_email, subject, html_body):
    api_key    = os.getenv("BREVO_API_KEY")
    from_email = os.getenv("GMAIL_FROM")

    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={"api-key": api_key, "Content-Type": "application/json"},
        json={
            "sender":      {"email": from_email},
            "to":          [{"email": to_email}],
            "subject":     subject,
            "htmlContent": html_body,
        },
        timeout=_TIMEOUT,
    )
    if not response.ok:
        raise RuntimeError(f"Brevo API HTTP {response.status_code}")
