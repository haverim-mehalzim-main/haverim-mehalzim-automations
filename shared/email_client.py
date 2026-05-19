import os
import requests


def send_email(to_email, subject, html_body):
    api_key   = os.getenv("BREVO_API_KEY")
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
    )
    if not response.ok:
        print("Brevo error:", response.status_code, response.text)
    response.raise_for_status()
