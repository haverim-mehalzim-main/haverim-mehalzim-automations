import os
import requests

_TIMEOUT = 30


def send_email(to_email, subject, html_body):
    api_key    = os.getenv("BREVO_API_KEY")
    from_email = os.getenv("GMAIL_FROM")

    # Support both single email (string) and multiple emails (list).
    recipients = to_email if isinstance(to_email, list) else [to_email]
    to_list = [{"email": email} for email in recipients]

    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={"api-key": api_key, "Content-Type": "application/json"},
        json={
            "sender":      {"name": os.getenv("GMAIL_FROM_NAME", "חברים מחלצים"), "email": from_email},
            "to":          to_list,
            "subject":     subject,
            "htmlContent": html_body,
        },
        timeout=_TIMEOUT,
    )
    if not response.ok:
        raise RuntimeError(f"Brevo API HTTP {response.status_code}")
