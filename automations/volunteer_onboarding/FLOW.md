# Volunteer Onboarding — Flow

## How it works

Every minute, an external cron service triggers the automation via GitHub Actions.
The script checks Monday.com for new volunteer registrations, processes each one end-to-end, and marks it as done.

---

## Flow Diagram

```mermaid
flowchart TD
    CRON([cron-job.org\nfires every minute])
    CRON -->|POST to GitHub API| GH[GitHub Actions\nspins up a runner]

    GH --> ENV{All required\nenv vars present?}
    ENV -->|No| CRASH[💥 Crash with\nclear error message]
    ENV -->|Yes| FETCH[Fetch all items from\nMonday.com registration board]

    FETCH -->|API error| ALERT_FETCH[📧 Send alert email\nto admin]
    FETCH -->|Success| FILTER[Filter out already-processed items\ncheckbox = checked]

    FILTER -->|Nothing new| DONE([✅ Done])
    FILTER -->|New registrations found| LOOP

    subgraph LOOP[" For each unprocessed volunteer "]
        direction TB
        EMAIL_CHECK{Has email\naddress?}
        EMAIL_CHECK -->|No| SKIP[📧 Alert admin\nskip volunteer]

        EMAIL_CHECK -->|Yes| WELCOME[📧 Send welcome email\nvia Brevo]
        WELCOME --> WA[💬 Send WhatsApp notification\nvia Whatsable]
        WA --> LLM[🤖 Claude AI\nmatches departments, skills,\nregion, FRTs]
        LLM -->|Empty response| RETRY[Retry once]
        RETRY -->|Still empty| EMPTY[Proceed with\nempty fields]
        RETRY -->|Success| CREATE
        EMPTY --> CREATE
        LLM -->|Success| CREATE[Create volunteer item\nin Monday.com volunteers board]
        CREATE --> MARK[✔️ Mark as processed\nin registration board]
    end

    LOOP -->|Any step fails| ALERT_VOL[📧 Alert admin\ncontinue to next volunteer]
    MARK --> FILTER
```

---

## Components

| Component | Role |
|---|---|
| **cron-job.org** | Fires every minute, calls GitHub API to trigger the workflow |
| **GitHub Actions** | Runs the Python script on a Ubuntu runner |
| **Monday.com (registration board)** | Source of new volunteer registrations |
| **Monday.com (volunteers board)** | Destination — where processed volunteers are stored |
| **Brevo** | Sends the welcome email to the volunteer |
| **Whatsable** | Sends a WhatsApp notification to the team |
| **Claude AI** | Reads the volunteer's form and infers their departments, skills, region, and FRTs |

---

## What "processed" means

Each item on the registration board has a hidden checkbox column.
- **Unchecked** → not yet processed, will be picked up on the next run
- **Checked** → already processed, will be skipped forever

The checkbox is only marked **after all steps succeed**. If anything fails mid-way, the item stays unchecked and the next run retries it automatically.

---

## Error handling

If any step fails for a volunteer:
1. An alert email is sent to the admin with the full error details
2. The volunteer's checkbox stays unchecked → retried on the next run
3. The script continues processing the remaining volunteers

If fetching the board itself fails, an alert is sent and the entire run exits cleanly.
