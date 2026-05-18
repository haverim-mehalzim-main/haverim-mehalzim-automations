import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

import anthropic
from dotenv import load_dotenv

from shared.monday_client import fetch_last_week_incidents

load_dotenv()

ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY")
GMAIL_FROM         = os.getenv("GMAIL_FROM")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RON_EMAIL          = os.getenv("RON_EMAIL")

INCIDENT_TYPES = {
    "רפואי":          "Medical",
    "נפשי":           "Mental Health",
    "חילוץ":          "Rescue",
    "איתור":          "Search & Locate",
    "אנטישמיות":      "Antisemitism",
    "חברות מחלצות":   "Sexual Assault",
    "אחר":            "Other",
}

HANDLED_STATUSES = {"נפתח אירוע", "טופל על ידי רון", "אירוע משמעותי"}


def format_incidents_for_prompt(incidents):
    lines = []
    for inc in incidents:
        inc_type = INCIDENT_TYPES.get(inc.get("status_mkmb1zc6", ""), inc.get("status_mkmb1zc6", "Unknown"))
        country = inc.get("country_mkmb91h3", "Unknown")
        timeline = inc.get("timeline_mkmbcabh", "")
        status = inc.get("color_mkvvrm1r", "")
        life_threatening = inc.get("check_mkn3c7v8", "")
        description = inc.get("text_mm2rhefh", "")
        assistance = inc.get("text_mm2rbp1q", "")
        handled = "Yes" if status in HANDLED_STATUSES else "No"

        parts = [
            f"Name: {inc.get('name', '')}",
            f"Type: {inc_type}",
            f"Country: {country}",
            f"Timeline: {timeline}",
            f"Handled: {handled}",
        ]
        if life_threatening:
            parts.append("LIFE-THREATENING: Yes")
        if description:
            parts.append(f"What happened: {description}")
        if assistance:
            parts.append(f"How we helped: {assistance}")

        lines.append(" | ".join(parts))

    return "\n".join(lines) if lines else "No incidents this week."


def generate_summary(incidents):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    week_end   = datetime.now().strftime("%B %d, %Y")
    week_start = (datetime.now() - timedelta(days=7)).strftime("%B %d")
    incidents_text = format_incidents_for_prompt(incidents)

    prompt = f"""You are preparing a weekly operational summary for Ron, director of Haverim Mehalzim — \
a volunteer emergency response organization that assists Jews in crisis situations worldwide.

Incidents from the past week ({week_start} – {week_end}):

{incidents_text}

Write a concise, professional summary. Structure it as:

1. **Overview** — total incidents, how many were handled
2. **Breakdown by type** — counts per category
3. **Countries** — which countries were involved
4. **Life-threatening cases** — highlight any and their outcomes
5. **Notable cases** — 1–2 sentences on anything significant
6. **Assessment** — one sentence on how the week went overall

Keep it under 300 words. Plain text, no markdown."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


def send_email(subject, body):
    msg = MIMEMultipart()
    msg["From"]    = GMAIL_FROM
    msg["To"]      = RON_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_FROM, GMAIL_APP_PASSWORD)
        server.send_message(msg)


def main():
    print("Fetching last week's incidents...")
    incidents = fetch_last_week_incidents()

    if incidents is None:
        print("Failed to fetch incidents — aborting.")
        return

    print(f"Found {len(incidents)} incidents. Generating summary...")
    summary = generate_summary(incidents)

    week_end   = datetime.now().strftime("%B %d, %Y")
    week_start = (datetime.now() - timedelta(days=7)).strftime("%B %d")
    subject = f"Haverim Mehalzim — Weekly Summary ({week_start}–{week_end})"

    print("Sending email...")
    send_email(subject, summary)
    print(f"Done. Summary sent to {RON_EMAIL}.")


if __name__ == "__main__":
    main()
