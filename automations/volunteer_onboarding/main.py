import os
import traceback
from datetime import datetime
from dotenv import load_dotenv

from shared.monday_client import fetch_board_items, mark_item_processed, create_board_item
from shared.email_client import send_email
from shared.whatsapp_client import send_whatsapp_message
from shared.llm_client import match_departments

load_dotenv()

REGISTRATION_BOARD_ID = os.getenv("REGISTRATION_BOARD_ID")
VOLUNTEERS_BOARD_ID   = os.getenv("VOLUNTEERS_BOARD_ID")
ADMIN_EMAIL           = os.getenv("ADMIN_EMAIL")

# Monday column IDs — not secrets, safe to hardcode in a public repo
PROCESSED_COLUMN_ID   = "boolean_mm3gnk59"

COL_SUMMARY           = "summary_mkmk881m"
COL_IS_ONBOARDED      = "status"
COL_SIGNED_AGREEMENT  = "status_mkmvpz7w"
COL_COUNTRY           = "text_mkmkf2zw"
COL_CITY              = "text_mkmkn993"
COL_REGION            = "region_of_activity_mkmrt3js"
COL_FIELDS            = "dropdown_mkkd6wx9"
COL_SKILLS            = "skills_mkmrt4a9"
COL_FRTS              = "frts_mkmrhrfj"
COL_PHONE             = "phone_mkkdavsh"
COL_MILITARY          = "text_mm1gjv5y"
COL_EMAIL             = "text_mkkf1tat"
COL_JOINED_AT         = "date4"
COL_LANGUAGES         = "text_1_mkmkd4xa"
COL_SOCIAL_MEDIA      = "text_mkmkhzp"
COL_IS_DONOR          = "color_mksekef4"
COL_ADDRESS           = "text_mm1gym24"
COL_REGISTRATION_LINK = "text_mm1gd18r"
COL_CREATED_AT        = "date_mkmkq362"
COL_UPDATED_AT        = "date_mkmkagv1"
COL_APPROVAL_CONTENT  = "color_mm1gbzk6"
COL_APPROVAL_LOCATION = "color_mm1gh4pt"
COL_MORE_DETAILS      = "text_mkmksedk"

_REQUIRED_ENV = [
    "MONDAY_API_KEY",
    "REGISTRATION_BOARD_ID",
    "VOLUNTEERS_BOARD_ID",
    "BREVO_API_KEY",
    "GMAIL_FROM",
    "ANTHROPIC_API_KEY",
    "ADMIN_EMAIL",
    "WHATSABLE_API_KEY",
    "PHONE_NUMBER",
]


def _validate_env():
    missing = [k for k in _REQUIRED_ENV if not os.getenv(k)]
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")


def _parse_date(date_str):
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return {"date": dt.strftime("%Y-%m-%d")}
    except Exception:
        return None


def is_processed(item):
    return bool(item.get(PROCESSED_COLUMN_ID, "").strip())


def _clean_link(value):
    """Monday link columns come back as ``"<label> - <url>"`` (e.g.
    ``"www.linkrfin.com - https://www.linkrfin.com"``), which shows the address
    twice. Collapse it to the single real URL. URLs never contain " - " (a space),
    so splitting on it is safe."""
    if not value:
        return ""
    parts = [p.strip() for p in str(value).split(" - ") if p.strip()]
    if not parts:
        return ""
    for p in parts:                       # prefer the part with an explicit scheme
        if "://" in p:
            return p
    return parts[-1]


def extract_volunteer(item):
    # Monday returns null (→ None) for empty columns, which would render as the
    # literal word "None". `g()` coerces any missing/null field to "".
    def g(key):
        val = item.get(key)
        return str(val) if val else ""

    return {
        "id":               g("id"),
        "name":             g("name"),
        "location":         g("short_text8m97hmsb"),
        "background":       g("long_text_mkqyb3me"),
        "military":         g("short_textryojenfq"),
        "interests":        " | ".join(filter(None, [
            g("multi_selectvzgzazus"),
            g("multi_selectxlqwrsg1"),
            g("multi_selectuhal084n"),
            g("multi_selecthdfth0p3"),
        ])),
        "linkedin":         _clean_link(g("linklmimmuok")),
        "phone":            g("phonef70cyv01"),
        "email":            g("emailc3bvh0j2"),
        "languages":        g("dropdown_mkqy9ym1"),
        "approval_content": g("single_select0lj8mys"),
        "approval_location":g("single_selectre9vtk2"),
        "created_at":       g("created_at"),
    }


def build_welcome_email(volunteer):
    name = volunteer["name"]
    return f"""<!DOCTYPE html>
<html dir="rtl" lang="he">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f0f2f5;font-family:Arial,sans-serif;direction:rtl;">
  <div style="max-width:600px;margin:32px auto;background:#fff;border-radius:10px;
              overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">

    <div style="background:linear-gradient(135deg,#1a252f 0%,#2c3e50 100%);padding:28px 32px;">
      <h1 style="margin:0;font-size:22px;color:#fff;font-weight:700;">חברים מחלצים 🤝</h1>
      <div style="margin-top:6px;font-size:14px;color:#bdc3c7;">Haverim Mehalzim</div>
    </div>

    <div style="padding:28px 32px;font-size:15px;line-height:1.8;color:#2c3e50;">
      <p>היי <strong>{name}</strong>!</p>

      <p>שמי לירן, ואני מתנדב בצוות הקהילה של חברים מחלצים.</p>

      <p>תודה שמילאת את טופס המתנדבים שלנו.<br>
      בשם הארגון, אני רוצה להגיד שאנחנו ממש שמחים על הרצון להצטרף אלינו. זה ממש לא מובן מאליו! 🙂</p>

      <p><strong>אז מה קורה עכשיו?</strong><br>
      בינתיים, אנחנו שומרים את הפרטים שמילאת, וכשיהיו תפקידים או משימות שמתאימים למה שציינת, ניצור קשר.</p>

      <p>עד אז, אפשר לפנות אלינו בכל שאלה, רעיון או מחשבה:<br>
      📧 <a href="mailto:info@haverimmehalzim.org">info@haverimmehalzim.org</a><br>
      📞 <a href="tel:+972506899026">+972 50-689-9026</a></p>

      <p>תודה על הבחירה להצטרף ולעשות טוב.<br>
      אנחנו כבר מחכים להזדמנות לפעול יחד!</p>

      <p><strong>לירן מצוות קהילת המתנדבים של חברים מחלצים</strong></p>
    </div>

    <div style="background:#f8f9fa;padding:16px 32px;text-align:center;
                font-size:12px;color:#95a5a6;border-top:1px solid #ecf0f1;">
      Haverim Mehalzim · <a href="mailto:info@haverimmehalzim.org">info@haverimmehalzim.org</a>
    </div>
  </div>
</body>
</html>"""


def _whatsapp_link(phone):
    """Turn a raw phone number into a wa.me link WhatsApp renders as a tappable
    chat link. Normalizes Israeli numbers (e.g. 050-123-4567 → 972501234567).

    Only ASCII digits 0-9 are kept, so the resulting URL host/path can never be
    influenced by form input — no URL/host injection is possible."""
    digits = "".join(ch for ch in str(phone) if ch in "0123456789")
    if digits.startswith("00"):          # international dialing prefix (00 + country code)
        digits = digits[2:]
    if not digits:
        return ""
    if not digits.startswith("972") and digits.startswith("0"):
        digits = "972" + digits[1:]      # local Israeli number → international
    return f"https://wa.me/{digits}"


def build_whatsapp_message(volunteer):
    phone      = volunteer['phone']
    phone_link = _whatsapp_link(phone)
    phone_line = f"מספר טלפון: {phone}"
    if phone_link:
        phone_line += f"\nצ'אט ישיר בוואטסאפ (לחצו): {phone_link}"
    return f"""מתנדב חדש מילא את הטופס שלנו!

שם: {volunteer['name']}
מיקום בשגרה: {volunteer['location']}
קצת רקע: {volunteer['background']}
רקע צבא / שירות לאומי: {volunteer['military']}
במה רוצה להתנדב: {volunteer['interests']}
חשבון לינקדאין: {volunteer['linkedin']}
{phone_line}
כתובת אימייל: {volunteer['email']}
שפות: {volunteer['languages']}

שימו לב שהמידע על המתנדב/ת מיד יעובד באמצעות מודל הAI שלנו ויוסיף את המתנדב/ת לתוך מאגר המתנדבים שלנו:
https://haverim-mehalzim.monday.com/boards/1752554957"""


def _safe_list(value):
    """Ensure LLM output is always a list, even if Claude returns a string."""
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value:
        return [value]
    return []


def _match_departments_with_retry(volunteer):
    result = match_departments(volunteer)
    if not result:
        print("  LLM returned empty — retrying once...")
        result = match_departments(volunteer)
    if not result:
        print("  LLM retry also failed — proceeding with empty fields")
        return {}
    return result


def _send_error_alert(name, error_details):
    subject = f"[Automation Error] Failed to process volunteer: {name}"
    body = f"""<!DOCTYPE html><html><body>
<p>The volunteer onboarding automation failed for <strong>{name}</strong>.</p>
<pre style="background:#f5f5f5;padding:12px;border-radius:4px;">{error_details}</pre>
<p>Please check the <a href="https://github.com/liranneta23/haverim-mehalzim-automations/actions">GitHub Actions logs</a>
and process this volunteer manually if needed.</p>
</body></html>"""
    try:
        send_email(ADMIN_EMAIL, subject, body)
    except Exception:
        print("  Also failed to send error alert email")


def build_volunteer_columns(volunteer, llm_result):
    created_date = _parse_date(volunteer.get("created_at"))

    cols = {
        COL_SUMMARY:           llm_result.get("summary", ""),
        COL_IS_ONBOARDED:      {"label": "Filled the form in"},
        COL_SIGNED_AGREEMENT:  {"label": "Yes"},
        COL_COUNTRY:           llm_result.get("country", ""),
        COL_CITY:              llm_result.get("city", ""),
        COL_REGION:            llm_result.get("region_of_activity", ""),
        COL_FIELDS:            {"labels": _safe_list(llm_result.get("fields"))},
        COL_SKILLS:            ", ".join(_safe_list(llm_result.get("skills"))),
        COL_FRTS:              ", ".join(_safe_list(llm_result.get("frts"))),
        COL_PHONE:             {"phone": volunteer.get("phone", ""), "countryShortName": ""},
        COL_MILITARY:          volunteer.get("military", ""),
        COL_EMAIL:             volunteer.get("email", ""),
        COL_LANGUAGES:         volunteer.get("languages", ""),
        COL_SOCIAL_MEDIA:      volunteer.get("linkedin", ""),
        COL_IS_DONOR:          {"label": "No"},
        COL_ADDRESS:           volunteer.get("location", ""),
        COL_REGISTRATION_LINK: (
            f"https://haverim-mehalzim.monday.com/boards/{REGISTRATION_BOARD_ID}"
            f"/pulses/{volunteer['id']}"
        ),
        COL_MORE_DETAILS:      "",
    }

    approval_content = volunteer.get("approval_content", "")
    if approval_content:
        cols[COL_APPROVAL_CONTENT] = {"label": approval_content}

    approval_location = volunteer.get("approval_location", "")
    if approval_location:
        cols[COL_APPROVAL_LOCATION] = {"label": approval_location}

    if created_date:
        cols[COL_JOINED_AT]  = created_date
        cols[COL_CREATED_AT] = created_date
        cols[COL_UPDATED_AT] = created_date

    return cols


def main():
    _validate_env()
    print("Checking for new volunteer registrations...")

    try:
        all_items = fetch_board_items(REGISTRATION_BOARD_ID)
    except Exception:
        error_details = traceback.format_exc()
        print("Failed to fetch board items — sending alert")
        _send_error_alert("N/A", f"Failed to fetch board items:\n{error_details}")
        return

    unprocessed = [item for item in all_items if not is_processed(item)]
    print(f"Found {len(unprocessed)} unprocessed registration(s).")

    failed_ids = []

    for item in unprocessed:
        volunteer = extract_volunteer(item)
        item_id   = item["id"]

        print(f"Processing item {item_id}")

        # ── Step 1: welcome email ─────────────────────────────────────────
        # The welcome email must never be sent twice, so the whole flow is
        # built around sending it exactly once. If it fails we do NOT mark the
        # item processed — the next run retries so the volunteer still gets it.
        try:
            if not volunteer["email"]:
                # Nothing to send without an address. Mark processed so we stop
                # re-alerting every minute, then flag for manual handling.
                mark_item_processed(item_id, REGISTRATION_BOARD_ID, PROCESSED_COLUMN_ID)
                raise ValueError("Volunteer has no email address — cannot send welcome email")

            send_email(
                volunteer["email"],
                "איזה כיף שהצטרפת אלינו! 🙌 | Welcome to our Community!",
                build_welcome_email(volunteer),
            )
            print(f"  ✓ Welcome email sent")
        except Exception:
            error_details = traceback.format_exc()
            print(f"  ERROR sending welcome email for item {item_id} — sending alert")
            failed_ids.append(item_id)
            _send_error_alert(volunteer["name"], error_details)
            continue

        # ── Step 2: lock immediately so the email can never be re-sent ─────
        try:
            mark_item_processed(item_id, REGISTRATION_BOARD_ID, PROCESSED_COLUMN_ID)
            print(f"  ✓ Marked as processed")
        except Exception:
            # If this fails the next run may re-send the welcome email. Alert
            # loudly, but still attempt the follow-up steps below.
            error_details = traceback.format_exc()
            print(f"  WARNING: could not mark item {item_id} processed — duplicate email risk")
            _send_error_alert(
                volunteer["name"],
                "Welcome email WAS sent but marking the registration processed FAILED — "
                "the next run may re-send the welcome email. Please mark it manually.\n\n"
                + error_details,
            )

        # ── Step 3: follow-up steps — best effort, no retry ────────────────
        # The email is sent and the row is locked, so a failure here must not
        # re-trigger the whole flow (which would duplicate the email, WhatsApp
        # message and board row). Alert the admin to finish this one manually.
        try:
            send_whatsapp_message(build_whatsapp_message(volunteer))
            print(f"  ✓ WhatsApp notification sent")

            llm_result = _match_departments_with_retry(volunteer)
            print(f"  ✓ LLM processing done")

            create_board_item(
                VOLUNTEERS_BOARD_ID,
                volunteer["name"],
                build_volunteer_columns(volunteer, llm_result),
            )
            print(f"  ✓ Created item in volunteers board")
            print(f"  ✓ Done: item {item_id}")
        except Exception:
            error_details = traceback.format_exc()
            print(f"  ERROR in follow-up steps for item {item_id} — sending alert")
            failed_ids.append(item_id)
            _send_error_alert(
                volunteer["name"],
                "Welcome email was sent and the registration is marked processed, "
                "but a follow-up step (WhatsApp / LLM / volunteers board) failed. "
                "Please complete this volunteer manually.\n\n" + error_details,
            )

    if failed_ids:
        print(f"\nFailed to process {len(failed_ids)} item(s): {', '.join(failed_ids)}")

    print("Finished.")


if __name__ == "__main__":
    main()
