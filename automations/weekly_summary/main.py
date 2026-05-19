import os
from collections import Counter
from datetime import datetime, timedelta

from dotenv import load_dotenv

from shared.monday_client import fetch_last_week_incidents
from shared.email_client import send_email

load_dotenv()

RON_EMAIL = os.getenv("RON_EMAIL")

INCIDENT_TYPES = {
    "רפואי":          "Medical",
    "נפשי":           "Mental Health",
    "חילוץ":          "Rescue",
    "איתור":          "Search & Locate",
    "אנטישמיות":      "Antisemitism",
    "חברות מחלצות":   "Sexual Assault",
    "אחר":            "Other",
}

HANDLED_STATUSES = {"נפתח אירוע", "טופל על ידי רון", "אירוע משמעותי"}

TYPE_COLORS = {
    "Medical":        "#e74c3c",
    "Mental Health":  "#9b59b6",
    "Rescue":         "#e67e22",
    "Search & Locate":"#3498db",
    "Antisemitism":   "#c0392b",
    "Sexual Assault": "#8e44ad",
    "Other":          "#7f8c8d",
}


def build_html_summary(incidents, week_start, week_end):
    total = len(incidents)
    handled = sum(1 for i in incidents if i.get("color_mkvvrm1r", "") in HANDLED_STATUSES)
    life_threatening = [i for i in incidents if i.get("check_mkn3c7v8", "")]

    type_counts = Counter()
    for inc in incidents:
        raw = inc.get("status_mkmb1zc6", "")
        type_counts[INCIDENT_TYPES.get(raw, "Other")] += 1

    country_counts = Counter()
    for inc in incidents:
        c = inc.get("country_mkmb91h3", "").strip()
        if c:
            country_counts[c] += 1

    notable = [
        i for i in incidents
        if i.get("text_mm2rhefh", "").strip() or i.get("text_mm2rbp1q", "").strip()
    ][:5]

    def section(title, content):
        return f"""
        <div style="margin-bottom:28px;">
          <h2 style="margin:0 0 12px;font-size:16px;color:#2c3e50;border-bottom:2px solid #3498db;
                     padding-bottom:6px;text-transform:uppercase;letter-spacing:0.5px;">{title}</h2>
          {content}
        </div>"""

    def stat_box(label, value, color="#3498db"):
        return f"""
        <div style="display:inline-block;background:{color};color:#fff;border-radius:8px;
                    padding:14px 22px;margin:0 8px 8px 0;text-align:center;min-width:90px;">
          <div style="font-size:28px;font-weight:700;line-height:1;">{value}</div>
          <div style="font-size:12px;margin-top:4px;opacity:0.9;">{label}</div>
        </div>"""

    overview_html = f"""
    <div style="margin-bottom:8px;">
      {stat_box("Total Incidents", total, "#2c3e50")}
      {stat_box("Handled", handled, "#27ae60")}
      {stat_box("Unhandled", total - handled, "#e74c3c")}
      {stat_box("Life-Threatening", len(life_threatening), "#c0392b")}
    </div>"""

    if type_counts:
        rows = "".join(
            f"""<tr>
              <td style="padding:8px 12px;border-bottom:1px solid #ecf0f1;">
                <span style="display:inline-block;width:10px;height:10px;border-radius:50%;
                             background:{TYPE_COLORS.get(t,'#95a5a6')};margin-right:8px;"></span>{t}
              </td>
              <td style="padding:8px 12px;border-bottom:1px solid #ecf0f1;font-weight:600;
                         color:{TYPE_COLORS.get(t,'#95a5a6')};">{n}</td>
            </tr>"""
            for t, n in type_counts.most_common()
        )
        types_html = f"""
        <table style="width:100%;border-collapse:collapse;font-size:14px;">
          <thead>
            <tr style="background:#f8f9fa;">
              <th style="padding:8px 12px;text-align:left;color:#666;font-weight:600;">Type</th>
              <th style="padding:8px 12px;text-align:left;color:#666;font-weight:600;">Count</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>"""
    else:
        types_html = "<p style='color:#666;font-size:14px;'>No incident types recorded.</p>"

    if country_counts:
        tags = "".join(
            f"""<span style="display:inline-block;background:#ecf0f1;border-radius:4px;
                            padding:4px 10px;margin:3px;font-size:13px;color:#2c3e50;">
              {c} <strong>({n})</strong></span>"""
            for c, n in country_counts.most_common()
        )
        countries_html = f"<div>{tags}</div>"
    else:
        countries_html = "<p style='color:#666;font-size:14px;'>No country data recorded.</p>"

    if life_threatening:
        lt_rows = "".join(
            f"""<div style="background:#fff5f5;border-left:4px solid #e74c3c;
                           padding:10px 14px;margin-bottom:8px;border-radius:0 6px 6px 0;">
              <div style="font-weight:600;color:#c0392b;margin-bottom:4px;">
                ⚠ {inc.get('name','')}
                <span style="font-weight:400;color:#888;font-size:12px;margin-left:8px;">
                  {INCIDENT_TYPES.get(inc.get('status_mkmb1zc6',''),'Unknown')} ·
                  {inc.get('country_mkmb91h3','')}
                </span>
              </div>
              {f'<div style="font-size:13px;color:#555;">{inc.get("text_mm2rhefh","")}</div>' if inc.get("text_mm2rhefh") else ''}
            </div>"""
            for inc in life_threatening
        )
        lt_html = lt_rows
    else:
        lt_html = "<p style='color:#27ae60;font-size:14px;'>No life-threatening incidents this week.</p>"

    if notable:
        notable_rows = "".join(
            f"""<div style="background:#f8f9fa;border-radius:6px;padding:12px 16px;margin-bottom:8px;">
              <div style="font-weight:600;color:#2c3e50;margin-bottom:6px;">
                {inc.get('name','')}
                <span style="font-weight:400;color:#888;font-size:12px;margin-left:8px;">
                  {INCIDENT_TYPES.get(inc.get('status_mkmb1zc6',''),'Unknown')} ·
                  {inc.get('country_mkmb91h3','')} ·
                  {inc.get('timeline_mkmbcabh','')}
                </span>
              </div>
              {f'<div style="font-size:13px;color:#555;margin-bottom:4px;"><strong>What happened:</strong> {inc.get("text_mm2rhefh","")}</div>' if inc.get("text_mm2rhefh") else ''}
              {f'<div style="font-size:13px;color:#27ae60;"><strong>How we helped:</strong> {inc.get("text_mm2rbp1q","")}</div>' if inc.get("text_mm2rbp1q") else ''}
            </div>"""
            for inc in notable
        )
        notable_html = notable_rows
    else:
        notable_html = "<p style='color:#666;font-size:14px;'>No detailed case notes this week.</p>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f0f2f5;font-family:Arial,sans-serif;">
  <div style="max-width:640px;margin:32px auto;background:#fff;border-radius:10px;
              overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#1a252f 0%,#2c3e50 100%);padding:28px 32px;">
      <div style="font-size:11px;color:#7f8c8d;text-transform:uppercase;letter-spacing:1px;
                  margin-bottom:6px;">Weekly Operational Report</div>
      <h1 style="margin:0;font-size:22px;color:#fff;font-weight:700;">
        Haverim Mehalzim
      </h1>
      <div style="margin-top:6px;font-size:14px;color:#bdc3c7;">
        {week_start} – {week_end}
      </div>
    </div>

    <!-- Body -->
    <div style="padding:28px 32px;">
      {section("Overview", overview_html)}
      {section("Breakdown by Type", types_html)}
      {section("Countries Involved", countries_html)}
      {section("Life-Threatening Cases", lt_html)}
      {section("Case Details", notable_html)}
    </div>

    <!-- Footer -->
    <div style="background:#f8f9fa;padding:16px 32px;text-align:center;
                font-size:12px;color:#95a5a6;border-top:1px solid #ecf0f1;">
      Haverim Mehalzim Automated Weekly Report · Generated {datetime.now().strftime("%B %d, %Y at %H:%M")}
    </div>
  </div>
</body>
</html>"""

    return html


def main():
    print("Fetching last week's incidents...")
    incidents = fetch_last_week_incidents()

    if incidents is None:
        print("Failed to fetch incidents — aborting.")
        return

    print(f"Found {len(incidents)} incidents. Building summary...")

    week_end   = datetime.now().strftime("%B %d, %Y")
    week_start = (datetime.now() - timedelta(days=7)).strftime("%B %d")

    html = build_html_summary(incidents, week_start, week_end)
    subject = f"Haverim Mehalzim — Weekly Summary ({week_start}–{week_end})"

    print("Sending email...")
    send_email(RON_EMAIL, subject, html)
    print("Done. Summary sent.")


if __name__ == "__main__":
    main()
