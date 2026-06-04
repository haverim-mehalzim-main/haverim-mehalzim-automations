"""Monthly stats email ("דוח חודשי").

Computes, over the last 30 days:
  • total volunteers + how many joined in the last 30 days ("הצטרפו בחודש האחרון")
  • number of incidents, broken down by type
  • number of countries we operated in

…then emails a polished Hebrew (RTL) report.

Run locally / test (override recipient):
    python -m automations.monthly_stats.main someone@example.com

Scheduled run (no arg → sends to SHAHAR_EMAIL):
    python -m automations.monthly_stats.main
"""

import os
import sys
from collections import Counter
from datetime import datetime, timedelta

from dotenv import load_dotenv

from shared.monday_client import fetch_all_board_items, fetch_incidents_in_range
from shared.email_client import send_email
from shared.incidents import labels, colors_by_label

load_dotenv()

VOLUNTEERS_BOARD_ID = os.getenv("VOLUNTEERS_BOARD_ID")
SHAHAR_EMAIL        = os.getenv("SHAHAR_EMAIL")

WINDOW_DAYS = 30

# Volunteers board join-date column (set by the onboarding automation).
COL_JOINED_AT = "date4"

# Incident type (status_mkmb1zc6) → Hebrew label / accent color.
_HE_LABELS = labels("he")
_HE_COLORS = colors_by_label("he")


def _fmt(n):
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return str(n or 0)


def _parse_date(value):
    """Parse a Monday date column ('YYYY-MM-DD') or an ISO created_at timestamp."""
    if not value:
        return None
    value = value.strip()
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d")
    except ValueError:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None


def compute_volunteer_stats(volunteers, cutoff):
    total = len(volunteers)
    joined_recent = 0
    for v in volunteers:
        joined = _parse_date(v.get(COL_JOINED_AT)) or _parse_date(v.get("created_at"))
        if joined and joined >= cutoff:
            joined_recent += 1
    return total, joined_recent


def compute_incident_stats(incidents):
    type_counts = Counter()
    for inc in incidents:
        raw = inc.get("status_mkmb1zc6", "")
        type_counts[_HE_LABELS.get(raw, "אחר")] += 1

    country_counts = Counter()
    for inc in incidents:
        c = (inc.get("country_mkmb91h3") or "").strip()
        if c:
            country_counts[c] += 1

    return type_counts, country_counts


# ── HTML ────────────────────────────────────────────────────────────────────

def _stat_tile(value, label, color):
    return f"""
      <td style="padding:8px;" align="center" valign="top">
        <div style="background:#f7f9fb;border:1px solid #eceff3;border-radius:12px;padding:18px 10px;">
          <div style="font-size:36px;font-weight:800;line-height:1;color:{color};">{value}</div>
          <div style="font-size:13px;color:#7f8c8d;margin-top:8px;">{label}</div>
        </div>
      </td>"""


def _color_for(label):
    return _HE_COLORS.get(label, "#7f8c8d")


def build_html(total_volunteers, joined_recent, total_incidents,
               type_counts, country_counts, start, end):
    period = f"{start.strftime('%d/%m/%Y')} – {end.strftime('%d/%m/%Y')}"

    stat_band = f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate;">
      <tr>
        {_stat_tile(_fmt(total_volunteers), "סה״כ מתנדבים", "#2c3e50")}
        {_stat_tile(_fmt(joined_recent), "הצטרפו בחודש האחרון", "#27AE60")}
        {_stat_tile(_fmt(total_incidents), "אירועים (30 יום)", "#E2574C")}
        {_stat_tile(_fmt(len(country_counts)), "מדינות פעילות", "#2E86C1")}
      </tr>
    </table>"""

    if type_counts:
        rows = ""
        for label, n in type_counts.most_common():
            color = _color_for(label)
            rows += f"""
            <tr>
              <td style="padding:9px 12px;border-bottom:1px solid #ecf0f1;font-size:14px;color:#2c3e50;">
                <span style="display:inline-block;width:10px;height:10px;border-radius:50%;
                             background:{color};margin-left:8px;"></span>{label}
              </td>
              <td style="padding:9px 12px;border-bottom:1px solid #ecf0f1;font-size:14px;
                         font-weight:700;color:{color};" align="left">{_fmt(n)}</td>
            </tr>"""
        types_html = f"""
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
          <tr style="background:#f8f9fa;">
            <th style="padding:9px 12px;text-align:right;color:#666;font-size:13px;font-weight:600;">סוג האירוע</th>
            <th style="padding:9px 12px;text-align:left;color:#666;font-size:13px;font-weight:600;">מספר</th>
          </tr>
          {rows}
        </table>"""
    else:
        types_html = '<p style="color:#95a5a6;font-size:14px;">לא נרשמו אירועים בתקופה זו.</p>'

    if country_counts:
        tags = "".join(
            f"""<span style="display:inline-block;background:#eef4f9;border-radius:6px;
                            padding:5px 11px;margin:3px;font-size:13px;color:#2c3e50;">
                  {c} <strong>({n})</strong></span>"""
            for c, n in country_counts.most_common()
        )
        countries_html = f"<div>{tags}</div>"
    else:
        countries_html = '<p style="color:#95a5a6;font-size:14px;">לא נרשמו מדינות בתקופה זו.</p>'

    def section(title, body):
        return f"""
        <div style="margin-top:28px;">
          <h2 style="margin:0 0 14px;font-size:17px;color:#1a252f;font-weight:700;
                     border-bottom:2px solid #E2574C;display:inline-block;padding-bottom:7px;">{title}</h2>
          {body}
        </div>"""

    generated = datetime.now().strftime("%d/%m/%Y")

    return f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#e9edf2;font-family:'Heebo',Arial,sans-serif;direction:rtl;">
  <div style="max-width:640px;margin:28px auto;background:#fff;border-radius:14px;
              overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">

    <div style="background:linear-gradient(135deg,#1a252f 0%,#2c3e50 100%);padding:30px 36px;">
      <div style="font-size:12px;letter-spacing:2px;color:#9fb1c1;text-transform:uppercase;">דוח חודשי</div>
      <h1 style="margin:6px 0 4px;font-size:26px;color:#fff;font-weight:800;">חברים מחלצים</h1>
      <div style="font-size:15px;color:#cdd7e0;">{period}</div>
    </div>

    <div style="padding:28px 36px;">
      {stat_band}
      {section("אירועים לפי סוג", types_html)}
      {section("מדינות בהן פעלנו", countries_html)}
    </div>

    <div style="background:#f7f9fb;padding:16px 36px;text-align:center;
                font-size:12px;color:#95a5a6;border-top:1px solid #eceff3;">
      חברים מחלצים · דוח חודשי אוטומטי · הופק בתאריך {generated}
    </div>
  </div>
</body>
</html>"""


def main():
    recipient = sys.argv[1] if len(sys.argv) > 1 else SHAHAR_EMAIL
    if not recipient:
        print("No recipient: pass one as an argument or set SHAHAR_EMAIL.")
        return
    if not VOLUNTEERS_BOARD_ID:
        print("VOLUNTEERS_BOARD_ID is not set.")
        return

    end    = datetime.now()
    start  = end - timedelta(days=WINDOW_DAYS)

    print("Fetching volunteers...")
    volunteers = fetch_all_board_items(VOLUNTEERS_BOARD_ID)
    total_volunteers, joined_recent = compute_volunteer_stats(volunteers, start)

    print(f"Fetching incidents {start:%Y-%m-%d} → {end:%Y-%m-%d}...")
    incidents = fetch_incidents_in_range(start, end)
    if incidents is None:
        print("Failed to fetch incidents from Monday — aborting.")
        return

    type_counts, country_counts = compute_incident_stats(incidents)
    total_incidents = len(incidents)

    print(f"volunteers={total_volunteers} joined_30d={joined_recent} "
          f"incidents={total_incidents} countries={len(country_counts)}")

    html = build_html(total_volunteers, joined_recent, total_incidents,
                      type_counts, country_counts, start, end)
    subject = f"חברים מחלצים — דוח חודשי ({start:%d/%m} – {end:%d/%m/%Y})"

    print(f"Sending report to {recipient}...")
    send_email(recipient, subject, html)
    print("Done. Report sent.")


if __name__ == "__main__":
    main()
