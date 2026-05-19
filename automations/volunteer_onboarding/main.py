import os
from datetime import datetime
from dotenv import load_dotenv

from shared.monday_client import fetch_board_items, mark_item_processed, create_board_item
from shared.email_client import send_email
from shared.whatsapp_client import send_whatsapp_message
from shared.llm_client import match_departments

load_dotenv()

REGISTRATION_BOARD_ID = os.getenv("REGISTRATION_BOARD_ID")
VOLUNTEERS_BOARD_ID   = os.getenv("VOLUNTEERS_BOARD_ID")

# Hardcoded — not secrets, just Monday column identifiers
PROCESSED_COLUMN_ID   = "boolean_mm3gnk59"

# Volunteers board column IDs
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


def extract_volunteer(item):
    return {
        "id":         item.get("id", ""),
        "name":       item.get("name", ""),
        "location":   item.get("short_text8m97hmsb", ""),
        "background": item.get("long_text_mkqyb3me", ""),
        "military":   item.get("short_textryojenfq", ""),
        "interests":  " | ".join(filter(None, [
            item.get("multi_selectvzgzazus", ""),
            item.get("multi_selectxlqwrsg1", ""),
            item.get("multi_selectuhal084n", ""),
            item.get("multi_selecthdfth0p3", ""),
        ])),
        "linkedin":   item.get("linklmimmuok", ""),
        "phone":      item.get("phonef70cyv01", ""),
        "email":      item.get("emailc3bvh0j2", ""),
        "languages":  item.get("dropdown_mkqy9ym1", ""),
        "created_at": item.get("created_at", ""),
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

      <p>ולסיום, זה הלינק להצטרפות לקהילה שלנו בוואטסאפ (לחצו בטלפון):<br>
      <a href="https://chat.whatsapp.com/D2xpFLpzfnVF6kZvCH9qMa">https://chat.whatsapp.com/D2xpFLpzfnVF6kZvCH9qMa</a></p>

      <p>תודה על הבחירה להצטרף ולעשות טוב.<br>
      אנחנו כבר מחכים להזדמנות לפעול יחד!</p>

      <p>באהבה,<br>
      <strong>לירן מצוות קהילת המתנדבים של חברים מחלצים</strong></p>
    </div>

    <div style="background:#f8f9fa;padding:16px 32px;text-align:center;
                font-size:12px;color:#95a5a6;border-top:1px solid #ecf0f1;">
      Haverim Mehalzim · <a href="mailto:info@haverimmehalzim.org">info@haverimmehalzim.org</a>
    </div>
  </div>
</body>
</html>"""


def build_whatsapp_message(volunteer):
    return f"""מתנדב חדש מילא את הטופס שלנו!

שם: {volunteer['name']}
מיקום בשגרה: {volunteer['location']}
קצת רקע: {volunteer['background']}
רקע צבא / שירות לאומי: {volunteer['military']}
במה רוצה להתנדב: {volunteer['interests']}
חשבון לינקדאין: {volunteer['linkedin']}
מספר טלפון: {volunteer['phone']}
כתובת אימייל: {volunteer['email']}
שפות: {volunteer['languages']}

שימו לב שהמידע על המתנדב/ת מיד יעובד באמצעות מודל הAI שלנו ויוסיף את המתנדב/ת לתוך מאגר המתנדבים שלנו:
https://haverim-mehalzim.monday.com/boards/1752554957"""


def build_volunteer_columns(volunteer, llm_result):
    created_date      = _parse_date(volunteer.get("created_at"))
    registration_link = (
        f"https://haverim-mehalzim.monday.com/boards/{REGISTRATION_BOARD_ID}"
        f"/pulses/{volunteer['id']}"
    )

    cols = {
        COL_SUMMARY:           llm_result.get("summary", ""),
        COL_IS_ONBOARDED:      {"label": "Filled the form in"},
        COL_SIGNED_AGREEMENT:  {"label": "Yes"},
        COL_COUNTRY:           llm_result.get("country", ""),
        COL_CITY:              llm_result.get("city", ""),
        COL_REGION:            llm_result.get("region_of_activity", ""),
        COL_FIELDS:            {"labels": llm_result.get("fields", [])},
        COL_SKILLS:            ", ".join(llm_result.get("skills", [])),
        COL_FRTS:              ", ".join(llm_result.get("frts", [])),
        COL_PHONE:             {"phone": volunteer.get("phone", ""), "countryShortName": ""},
        COL_MILITARY:          volunteer.get("military", ""),
        COL_EMAIL:             volunteer.get("email", ""),
        COL_LANGUAGES:         volunteer.get("languages", ""),
        COL_SOCIAL_MEDIA:      volunteer.get("linkedin", ""),
        COL_IS_DONOR:          {"label": "No"},
        COL_ADDRESS:           volunteer.get("location", ""),
        COL_REGISTRATION_LINK: registration_link,
    }

    if created_date:
        cols[COL_JOINED_AT]  = created_date
        cols[COL_CREATED_AT] = created_date
        cols[COL_UPDATED_AT] = created_date

    return cols


def main():
    print("Checking for new volunteer registrations...")

    all_items   = fetch_board_items(REGISTRATION_BOARD_ID)
    unprocessed = [item for item in all_items if not is_processed(item)]

    print(f"Found {len(unprocessed)} unprocessed registration(s).")

    for item in unprocessed:
        volunteer = extract_volunteer(item)
        name  = volunteer["name"]
        email = volunteer["email"]

        print(f"Processing: {name}")

        # Step 1: Welcome email
        send_email(
            email,
            "איזה כיף שהצטרפת אלינו! 🙌 | Welcome to our Community!",
            build_welcome_email(volunteer),
        )
        print(f"  ✓ Welcome email sent to {email}")

        # Step 2: WhatsApp notification
        send_whatsapp_message(build_whatsapp_message(volunteer))
        print(f"  ✓ WhatsApp notification sent")

        # Step 3: LLM department matching
        llm_result = match_departments(volunteer)
        print(f"  ✓ LLM processing done")

        # Step 4: Create item in volunteers board
        create_board_item(
            VOLUNTEERS_BOARD_ID,
            name,
            build_volunteer_columns(volunteer, llm_result),
        )
        print(f"  ✓ Created item in volunteers board")

        # Step 5: Mark as processed in registration board
        mark_item_processed(item["id"], REGISTRATION_BOARD_ID, PROCESSED_COLUMN_ID)
        print(f"  ✓ Marked as processed")

        print(f"  Done: {name}")

    print("Finished.")


if __name__ == "__main__":
    main()
