import os
import json
import requests
from datetime import datetime, timedelta

MONDAY_URL = "https://api.monday.com/v2"


def _headers():
    return {"Authorization": os.getenv("MONDAY_API_KEY"), "Content-Type": "application/json"}


def _run_query(query, variables=None):
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    response = requests.post(MONDAY_URL, json=payload, headers=_headers())
    if response.status_code != 200:
        print(f"HTTP {response.status_code}: {response.text}")
        return None
    data = response.json()
    if "errors" in data:
        print("GraphQL error:", data["errors"])
        return None
    return data["data"]


# ── Generic helpers ───────────────────────────────────────────────────────────

def fetch_board_items(board_id):
    query = """
    query($board_id: [ID!]) {
      boards(ids: $board_id) {
        items_page(limit: 500) {
          items {
            id
            name
            created_at
            column_values {
              id
              text
            }
          }
        }
      }
    }
    """
    data = _run_query(query, {"board_id": [str(board_id)]})
    if not data:
        return []
    items = data["boards"][0]["items_page"]["items"]
    results = []
    for item in items:
        row = {"id": item["id"], "name": item["name"], "created_at": item.get("created_at", "")}
        for cv in item["column_values"]:
            row[cv["id"]] = cv["text"]
        results.append(row)
    return results


def fetch_item_by_id(item_id):
    query = """
    query($item_id: [ID!]) {
      items(ids: $item_id) {
        id
        name
        column_values {
          id
          text
          value
        }
      }
    }
    """
    data = _run_query(query, {"item_id": [str(item_id)]})
    if not data or not data["items"]:
        return None
    item = data["items"][0]
    row = {"id": item["id"], "name": item["name"]}
    for cv in item["column_values"]:
        row[cv["id"]] = cv["text"]
    return row


def mark_item_processed(item_id, board_id, column_id):
    query = """
    mutation($item_id: ID!, $board_id: ID!, $column_id: String!, $value: JSON!) {
      change_column_value(item_id: $item_id, board_id: $board_id, column_id: $column_id, value: $value) {
        id
      }
    }
    """
    _run_query(query, {
        "item_id":   str(item_id),
        "board_id":  str(board_id),
        "column_id": column_id,
        "value":     json.dumps({"checked": "true"}),
    })


def create_board_item(board_id, item_name, column_values: dict):
    query = """
    mutation($board_id: ID!, $item_name: String!, $column_values: JSON!) {
      create_item(board_id: $board_id, item_name: $item_name, column_values: $column_values) {
        id
      }
    }
    """
    data = _run_query(query, {
        "board_id":      str(board_id),
        "item_name":     item_name,
        "column_values": json.dumps(column_values),
    })
    if data:
        return data["create_item"]["id"]
    return None


# ── Weekly summary (incidents board) ─────────────────────────────────────────

_INCIDENT_COLUMNS = [
    "color_mkvvrm1r",
    "status_mkmb1zc6",
    "country_mkmb91h3",
    "check_mkn3c7v8",
    "timeline_mkmbcabh",
    "text_mm2rhefh",
    "text_mm2rbp1q",
]

_COL_IDS = ", ".join(f'"{c}"' for c in _INCIDENT_COLUMNS)


def _build_incidents_query(board_id):
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
    board_id = os.getenv("BOARD_ID")
    cutoff   = datetime.now() - timedelta(days=7)

    if not board_id:
        print("BOARD_ID environment variable is not set.")
        return None

    try:
        response = requests.post(
            MONDAY_URL,
            json={"query": _build_incidents_query(board_id)},
            headers=_headers(),
        )

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
                start_str  = timeline.split(" - ")[0].strip()
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
