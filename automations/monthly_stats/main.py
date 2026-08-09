"""Monthly impact report ("דוח חודשי").

Shows, side by side, both this-month activity and all-time cumulative totals,
emailed on the last day of each month.

Headline stats (big number = all-time total, green chip = this month):
  • registered volunteers ("מתנדבים רשומים")  +joined this month
  • complicated cases managed — incidents whose handling status is an event
    ("מקרים מורכבים שטופלו")  +managed this month
  • countries we have operated in ("מדינות בהן פעלנו")  +active this month
  • WhatsApp community members  ← filled in manually by the recipient
  • total WhatsApp conversations ← filled in manually by the recipient

…plus a by-type breakdown (this month vs. total) and a list of countries.

Run locally / test (override recipients):
    python -m automations.monthly_stats.main someone@example.com

Scheduled run (no arg → sends to SHAHAR_EMAIL and RON_EMAIL):
    python -m automations.monthly_stats.main
"""

import os
import sys
from collections import Counter
from datetime import datetime, timedelta

from dotenv import load_dotenv

from shared.monday_client import fetch_all_board_items
from shared.email_client import send_email
from shared.incidents import labels, colors_by_label, EVENT_STATUSES

# Force UTF-8 console output so Hebrew / "→" don't crash on Windows (cp1252).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

load_dotenv()

VOLUNTEERS_BOARD_ID = os.getenv("VOLUNTEERS_BOARD_ID")
BOARD_ID            = os.getenv("BOARD_ID")            # incidents board
SHAHAR_EMAIL        = os.getenv("SHAHAR_EMAIL")
RON_EMAIL           = os.getenv("RON_EMAIL")

# Volunteers board join-date column (set by the onboarding automation).
COL_JOINED_AT = "date4"

# Incidents board columns.
COL_TYPE     = "status_mkmb1zc6"     # incident type (רפואי / חילוץ / …)
COL_EVENT    = "color_mkvvrm1r"      # handling status (נפתח אירוע / טופל …)
COL_COUNTRY  = "country_mkmb91h3"    # country
COL_TIMELINE = "timeline_mkmbcabh"   # incident date range "YYYY-MM-DD - YYYY-MM-DD"

# Incident type (status_mkmb1zc6) → Hebrew label / accent color.
_HE_LABELS = labels("he")
_HE_COLORS = colors_by_label("he")

# WhatsApp brand green, used for the manual-entry tiles and the "this month" chips.
_WA_GREEN = "#1e8449"

# Incidents/cases handled by us but never recorded on the board (managed
# offline / historically). Surfaced as a bracketed footnote on those tiles.
UNTRACKED_MANAGED = 32
_UNTRACKED_NOTE   = f"(+{UNTRACKED_MANAGED} שטופלו ולא תועדו)"


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


def _incident_date(inc):
    """Start date of an incident, read from its timeline column."""
    timeline = (inc.get(COL_TIMELINE) or "").strip()
    if " - " in timeline:
        timeline = timeline.split(" - ")[0].strip()
    return _parse_date(timeline)


def compute_volunteer_stats(volunteers, month_start, as_of):
    total = len(volunteers)
    joined_this_month = 0
    for v in volunteers:
        joined = _parse_date(v.get(COL_JOINED_AT)) or _parse_date(v.get("created_at"))
        if joined and month_start <= joined <= as_of:
            joined_this_month += 1
    return total, joined_this_month


def compute_incident_stats(incidents, month_start, as_of):
    """All-time + this-month stats from every incident on the board.

    Managed cases (and their by-type breakdown) cover incidents whose handling
    status is in EVENT_STATUSES; countries cover every incident with a country.
    """
    def is_this_month(inc):
        d = _incident_date(inc)
        return d is not None and month_start <= d <= as_of

    managed = [inc for inc in incidents if (inc.get(COL_EVENT) or "").strip() in EVENT_STATUSES]

    type_total = Counter()
    type_month = Counter()
    for inc in managed:
        label = _HE_LABELS.get((inc.get(COL_TYPE) or "").strip(), "אחר")
        type_total[label] += 1
        if is_this_month(inc):
            type_month[label] += 1

    country_total = Counter()
    country_month = Counter()
    for inc in incidents:
        c = (inc.get(COL_COUNTRY) or "").strip()
        if not c:
            continue
        country_total[c] += 1
        if is_this_month(inc):
            country_month[c] += 1

    # All incidents — no handling-status filter, including ones we didn't open
    # a case for. This is the superset of the "managed cases" count above.
    incidents_total = len(incidents)
    incidents_month = sum(1 for inc in incidents if is_this_month(inc))

    return {
        "incidents_total": incidents_total,
        "incidents_month": incidents_month,
        "cases_total":   len(managed),
        "cases_month":   sum(type_month.values()),
        "type_total":    type_total,
        "type_month":    type_month,
        "country_total": country_total,
        "country_month": country_month,
    }


# ── HTML ────────────────────────────────────────────────────────────────────

def _color_for(label):
    return _HE_COLORS.get(label, "#7f8c8d")


def _chip(text, *, bg="#eafaf1", color=_WA_GREEN):
    return (f'<div style="display:inline-block;background:{bg};color:{color};'
            f'font-size:11px;font-weight:700;border-radius:20px;padding:3px 10px;'
            f'margin-top:10px;">{text}</div>')


def _tile(value, label, color, width, *, big=False, note=None, badge=None, delta=None, sub=None):
    num_size   = "40px" if big else "34px"
    badge_html = ("" if not badge else
                  f'<div style="margin-bottom:10px;">{_chip(badge)}</div>')
    sub_html   = ("" if not sub else
                  f'<div style="font-size:11px;color:#9aa7b2;margin-top:5px;">{sub}</div>')
    note_html  = ("" if not note else
                  f'<div style="font-size:11px;color:#9aa7b2;margin-top:10px;line-height:1.6;">{note}</div>')
    delta_html = "" if not delta else _chip(delta)
    return f"""
      <td width="{width}" style="padding:8px;" align="center" valign="top">
        <div style="background:#f7f9fb;border:1px solid #eceff3;border-radius:14px;padding:22px 12px;">
          {badge_html}
          <div style="font-size:{num_size};font-weight:800;line-height:1;color:{color};">{value}</div>
          {sub_html}
          <div style="font-size:13px;color:#7f8c8d;margin-top:9px;font-weight:600;">{label}</div>
          {delta_html}{note_html}
        </div>
      </td>"""


def _section(title, body):
    return f"""
    <div style="margin-top:30px;">
      <h2 style="margin:0 0 14px;font-size:17px;color:#1a252f;font-weight:700;
                 border-bottom:2px solid #E2574C;display:inline-block;padding-bottom:7px;">{title}</h2>
      {body}
    </div>"""


def build_html(registered_volunteers, joined_this_month, inc, as_of):
    incidents_total = inc["incidents_total"]
    incidents_month = inc["incidents_month"]
    cases_total   = inc["cases_total"]
    cases_month   = inc["cases_month"]
    type_total    = inc["type_total"]
    type_month    = inc["type_month"]
    country_total = inc["country_total"]
    country_month = inc["country_month"]

    # ── Headline tiles: cumulative number + this-month chip ───────────────────
    hero = f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate;">
      <tr>
        {_tile(_fmt(registered_volunteers), "מתנדבים רשומים", "#2c3e50", "25%",
               big=True, delta=f"+{_fmt(joined_this_month)} החודש")}
        {_tile(_fmt(incidents_total), "סה״כ אירועים", "#E67E22", "25%",
               big=True, sub=_UNTRACKED_NOTE, delta=f"+{_fmt(incidents_month)} החודש")}
        {_tile(_fmt(cases_total), "מקרים מורכבים שטופלו", "#E2574C", "25%",
               big=True, sub=_UNTRACKED_NOTE, delta=f"+{_fmt(cases_month)} החודש")}
        {_tile(_fmt(len(country_total)), "מדינות בהן פעלנו", "#2E86C1", "25%",
               big=True, delta=f"{_fmt(len(country_month))} החודש")}
      </tr>
    </table>
    <div style="text-align:center;font-size:11px;color:#9aa7b2;margin-top:6px;">
      המספר הגדול = סה״כ מאז ההקמה · התווית הירוקה = פעילות החודש
    </div>"""

    # ── WhatsApp block: 2 manual-entry tiles ─────────────────────────────────
    whatsapp = f"""
    <div style="margin-top:22px;background:#f3fbf6;border:1px solid #d8f0e2;border-radius:16px;padding:8px 12px 14px;">
      <div style="padding:14px 8px 4px;font-size:15px;font-weight:700;color:{_WA_GREEN};">
        💬 קהילת הוואטסאפ
      </div>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate;">
        <tr>
          {_tile("—", "חברי קהילת הוואטסאפ", _WA_GREEN, "50%",
                 note="למילוי ידני — מספר החברים בקבוצת/קהילת הוואטסאפ", badge="✍️ לעדכון")}
          {_tile("—", "סה״כ שיחות בוואטסאפ", _WA_GREEN, "50%",
                 note="למילוי ידני — ספירת מספר השיחות בחשבון ה-WhatsApp Business", badge="✍️ לעדכון")}
        </tr>
      </table>
    </div>"""

    # ── Cases by type: this month vs. total ──────────────────────────────────
    if type_total:
        rows = ""
        for label, n in type_total.most_common():
            color = _color_for(label)
            rows += f"""
            <tr>
              <td style="padding:9px 12px;border-bottom:1px solid #ecf0f1;font-size:14px;color:#2c3e50;">
                <span style="display:inline-block;width:10px;height:10px;border-radius:50%;
                             background:{color};margin-left:8px;"></span>{label}
              </td>
              <td style="padding:9px 12px;border-bottom:1px solid #ecf0f1;font-size:14px;
                         color:{_WA_GREEN};font-weight:700;" align="center">{_fmt(type_month.get(label, 0))}</td>
              <td style="padding:9px 12px;border-bottom:1px solid #ecf0f1;font-size:14px;
                         font-weight:700;color:{color};" align="center">{_fmt(n)}</td>
            </tr>"""
        types_html = f"""
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
          <tr style="background:#f8f9fa;">
            <th style="padding:9px 12px;text-align:right;color:#666;font-size:13px;font-weight:600;">סוג המקרה</th>
            <th style="padding:9px 12px;text-align:center;color:{_WA_GREEN};font-size:13px;font-weight:700;">החודש</th>
            <th style="padding:9px 12px;text-align:center;color:#666;font-size:13px;font-weight:600;">סה״כ</th>
          </tr>
          {rows}
          <tr style="background:#fbfcfd;">
            <td style="padding:10px 12px;font-size:14px;font-weight:800;color:#1a252f;">סה״כ</td>
            <td style="padding:10px 12px;font-size:14px;font-weight:800;color:{_WA_GREEN};" align="center">{_fmt(cases_month)}</td>
            <td style="padding:10px 12px;font-size:14px;font-weight:800;color:#1a252f;" align="center">{_fmt(cases_total)}</td>
          </tr>
        </table>"""
    else:
        types_html = '<p style="color:#95a5a6;font-size:14px;">לא נרשמו מקרים מטופלים.</p>'

    # ── Countries: cumulative, with this-month ones highlighted ──────────────
    if country_total:
        tags = ""
        for c, n in country_total.most_common():
            active = c in country_month
            border = f"1px solid {_WA_GREEN}" if active else "1px solid #e3eaf1"
            bg     = "#eafaf1" if active else "#eef4f9"
            dot    = (f'<span style="display:inline-block;width:7px;height:7px;border-radius:50%;'
                      f'background:{_WA_GREEN};margin-left:6px;"></span>' if active else "")
            tags += (f'<span style="display:inline-block;background:{bg};border:{border};border-radius:6px;'
                     f'padding:5px 11px;margin:3px;font-size:13px;color:#2c3e50;">'
                     f'{dot}{c} <strong>({n})</strong></span>')
        caption = (f'<div style="font-size:12px;color:#7f8c8d;margin-bottom:10px;">'
                   f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;'
                   f'background:{_WA_GREEN};margin-left:6px;"></span>'
                   f'מתוכן, החודש פעלנו ב-{_fmt(len(country_month))} מדינות</div>')
        countries_html = caption + f"<div>{tags}</div>"
    else:
        countries_html = '<p style="color:#95a5a6;font-size:14px;">לא נרשמו מדינות.</p>'

    generated = as_of.strftime("%d/%m/%Y")

    return f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#e9edf2;font-family:'Heebo',Arial,sans-serif;direction:rtl;">
  <div style="max-width:640px;margin:28px auto;background:#fff;border-radius:14px;
              overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">

    <div style="background:linear-gradient(135deg,#1a252f 0%,#2c3e50 100%);padding:30px 36px;">
      <div style="font-size:12px;letter-spacing:2px;color:#9fb1c1;text-transform:uppercase;">דוח חודשי</div>
      <h1 style="margin:6px 0 4px;font-size:26px;color:#fff;font-weight:800;">חברים מחלצים</h1>
      <div style="font-size:15px;color:#cdd7e0;">חודש {as_of:%m/%Y} · החודש מול המצטבר · נכון ל-{generated}</div>
    </div>

    <div style="padding:28px 36px;">
      {hero}
      {whatsapp}
      {_section("מקרים מורכבים לפי סוג", types_html)}
      {_section("מדינות בהן פעלנו", countries_html)}
    </div>

    <div style="background:#f7f9fb;padding:16px 36px;text-align:center;
                font-size:12px;color:#95a5a6;border-top:1px solid #eceff3;">
      חברים מחלצים · דוח חודשי אוטומטי · הופק בתאריך {generated}
    </div>
  </div>
</body>
</html>"""


def _is_last_day_of_month(now):
    """True if `now` falls on the final calendar day of its month."""
    return (now + timedelta(days=1)).day == 1


def main():
    test_recipient = sys.argv[1] if len(sys.argv) > 1 else None
    if test_recipient:
        recipients = [test_recipient]
    else:
        recipients = [email for email in [SHAHAR_EMAIL, RON_EMAIL] if email]

    if not recipients:
        print("No recipients: pass one as an argument or set SHAHAR_EMAIL and/or RON_EMAIL.")
        return
    if not VOLUNTEERS_BOARD_ID:
        print("VOLUNTEERS_BOARD_ID is not set.")
        return
    if not BOARD_ID:
        print("BOARD_ID is not set.")
        return

    # Scheduled (prod) runs only fire on the last day of the month — the cron
    # trigger runs daily and this guard skips every other day. A test-send
    # (explicit recipient argument) always runs.
    if not test_recipient and not _is_last_day_of_month(datetime.now()):
        print(f"Not the last day of the month ({datetime.now():%Y-%m-%d}) — skipping.")
        return

    as_of       = datetime.now()
    month_start = as_of.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    print("Fetching volunteers...")
    volunteers = fetch_all_board_items(VOLUNTEERS_BOARD_ID)
    registered_volunteers, joined_this_month = compute_volunteer_stats(volunteers, month_start, as_of)

    print("Fetching all incidents (all-time)...")
    incidents = fetch_all_board_items(BOARD_ID)
    inc = compute_incident_stats(incidents, month_start, as_of)

    print(f"volunteers={registered_volunteers} (+{joined_this_month} this month) "
          f"incidents={inc['incidents_total']} (+{inc['incidents_month']} this month) "
          f"cases={inc['cases_total']} (+{inc['cases_month']} this month) "
          f"countries={len(inc['country_total'])} (+{len(inc['country_month'])} this month)")

    html = build_html(registered_volunteers, joined_this_month, inc, as_of)
    subject = f"חברים מחלצים — דוח חודשי ({as_of:%m/%Y})"

    print(f"Sending report to {', '.join(recipients)}...")
    send_email(recipients, subject, html)
    print("Done. Report sent.")


if __name__ == "__main__":
    main()
