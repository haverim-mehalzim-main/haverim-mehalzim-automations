import os
import requests
from datetime import datetime, timedelta

MONDAY_URL = "https://api.monday.com/v2"

_COLUMNS = [
    "color_mkvvrm1r",    # incident status (Hebrew)
    "status_mkmb1zc6",   # incident type
    "country_mkmb91h3",  # country
    "check_mkn3c7v8",    # life-threatening flag
    "timeline_mkmbcabh", # date range (YYYY-MM-DD - YYYY-MM-DD)
    "text_mm2rhefh",     # what happened
    "text_mm2rbp1q",     # how we helped
]

_COL_IDS = ", ".join(f'"{c}"' for c in _COLUMNS)


def _build_query(board_id):
    return """
{
  boards(ids: [%s]) {
    items_page(limit: 500) {
      items {
        id
        name
        column_values(ids: [%s]) {
          id
          text
        }
      }
    }
  }
}
""" % (board_id, _COL_IDS)


def fetch_last_week_incidents():
    api_key = os.getenv("MONDAY_API_KEY")
    board_id = os.getenv("BOARD_ID")
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    cutoff = datetime.now() - timedelta(days=7)

    if not board_id:
        print("BOARD_ID environment variable is not set.")
        return None

    query = _build_query(board_id)

    try:
        response = requests.post(MONDAY_URL, json={"query": query}, headers=headers)

        if response.status_code != 200:
            print(f"HTTP {response.status_code}: {response.text}")
            return None

        data = response.json()

        if "errors" in data:
            print("GraphQL error:", data["errors"])
            return None

        items = data["data"]["boards"][0]["items_page"]["items"]
        results = []

        for item in items:
            row = {"name": item["name"], "id": item["id"]}
            for cv in item["column_values"]:
                row[cv["id"]] = cv["text"]

            timeline = row.get("timeline_mkmbcabh", "")
            if not timeline or " - " not in timeline:
                continue

            try:
                start_str = timeline.split(" - ")[0].strip()
                start_date = datetime.strptime(start_str, "%Y-%m-%d")
                if start_date >= cutoff:
                    results.append(row)
            except ValueError:
                continue

        print(f"[monday_client] total={len(items)} last_week={len(results)}")
        return results

    except Exception as e:
        print(f"Error fetching Monday data: {e}")
        return None
