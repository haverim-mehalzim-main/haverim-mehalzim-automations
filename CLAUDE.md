# Haverim Mehalzim — Automations

## How it works

Each automation is a standalone Python script triggered by a GitHub Actions workflow.
The repo is public so GitHub Actions runs are **unlimited and free**.

## Folder structure

```
automations/
  weekly_summary/main.py        ← runs every Friday at 12:00 Israel time
  volunteer_onboarding/main.py  ← runs every 5 minutes, processes new registrations
shared/
  monday_client.py   ← Monday.com API: fetch items, create items, mark processed
  email_client.py    ← Brevo: send HTML emails
  llm_client.py      ← Claude AI: department matching
  whatsapp_client.py ← Whatsable: WhatsApp notifications
.github/workflows/
  weekly-summary.yml
  volunteer-onboarding.yml
```

## Adding a new automation

1. Create `automations/your_automation/__init__.py` (empty)
2. Create `automations/your_automation/main.py` (copy an existing one as a template)
3. Create `.github/workflows/your-automation.yml` (copy an existing workflow as a template)
4. Add any new secrets to GitHub → Settings → Secrets and Variables → Actions
5. Add new env vars to your local `.env`

## Running locally

```bash
python -m automations.weekly_summary.main
python -m automations.volunteer_onboarding.main
```

## Secrets

All secrets live in **GitHub repo Settings → Secrets and Variables → Actions**.
Never hardcode secrets in the code — always use `os.getenv("SECRET_NAME")`.

For local development, create a `.env` file (already in `.gitignore`) with your values.

## Required secrets

| Secret | Used by |
|--------|---------|
| `MONDAY_API_KEY` | All automations |
| `BOARD_ID` | Weekly summary |
| `REGISTRATION_BOARD_ID` | Volunteer onboarding |
| `VOLUNTEERS_BOARD_ID` | Volunteer onboarding |
| `BREVO_API_KEY` | All automations |
| `GMAIL_FROM` | All automations (sender email address, must be verified in Brevo) |
| `GMAIL_FROM_NAME` | All automations (sender display name, e.g. "חברים מחלצים") |
| `RON_EMAIL` | Weekly summary |
| `ANTHROPIC_API_KEY` | Volunteer onboarding |
| `ADMIN_EMAIL` | Volunteer onboarding (error alert recipient) |
| `WHATSABLE_API_KEY` | Volunteer onboarding |
| `PHONE_NUMBER` | Volunteer onboarding (WhatsApp notification recipient) |
