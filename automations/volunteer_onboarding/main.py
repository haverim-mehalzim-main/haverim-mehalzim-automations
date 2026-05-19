import os
from dotenv import load_dotenv

from shared.monday_client import fetch_item_by_id, mark_item_processed, create_board_item
from shared.email_client import send_email
from shared.whatsapp_client import send_whatsapp_message
from shared.llm_client import match_departments

load_dotenv()

REGISTRATION_BOARD_ID = os.getenv("REGISTRATION_BOARD_ID")
VOLUNTEERS_BOARD_ID   = os.getenv("VOLUNTEERS_BOARD_ID")
PROCESSED_COLUMN_ID   = os.getenv("PROCESSED_COLUMN_ID")


def main():
    item_id = os.getenv("VOLUNTEER_ITEM_ID")
    if not item_id:
        print("No VOLUNTEER_ITEM_ID provided.")
        return

    print(f"Processing volunteer item {item_id}...")

    volunteer = fetch_item_by_id(item_id)
    if not volunteer:
        print(f"Could not fetch item {item_id} from Monday.")
        return

    name  = volunteer.get("name", "")
    email = volunteer.get("email", "")  # TODO: replace with actual Monday column ID

    print(f"Volunteer: {name} ({email})")

    # Step 1: Send welcome email
    # TODO: uncomment and fill in when email content is provided
    # send_email(email, "ברוכים הבאים לחברים מהלב!", build_welcome_email(volunteer))
    print(f"[TODO] Send welcome email to {email}")

    # Step 2: WhatsApp notification
    # TODO: uncomment and fill in when message template is provided
    # send_whatsapp_message(f"מתנדב חדש נרשם: {name}")
    print(f"[TODO] Send WhatsApp notification for {name}")

    # Step 3: LLM department matching
    # TODO: uncomment when prompt is provided
    # departments = match_departments(volunteer)
    print(f"[TODO] LLM department matching for {name}")

    # Step 4: Create item in volunteers board
    # TODO: uncomment and map columns when board structure is known
    # create_board_item(VOLUNTEERS_BOARD_ID, name, {"department": departments})
    print(f"[TODO] Create item in volunteers board for {name}")

    # Step 5: Mark as processed in registration board
    mark_item_processed(item_id, REGISTRATION_BOARD_ID, PROCESSED_COLUMN_ID)

    print(f"Done: {name}")


if __name__ == "__main__":
    main()
