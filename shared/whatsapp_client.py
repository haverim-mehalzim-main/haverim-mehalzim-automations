import os
import requests


def send_whatsapp_message(message: str):
    # TODO: implement when Whatsable API details are provided
    api_key  = os.getenv("WHATSABLE_API_KEY")
    group_id = os.getenv("WHATSABLE_GROUP_ID")

    print(f"[whatsapp] TODO: send message when API details are provided")
