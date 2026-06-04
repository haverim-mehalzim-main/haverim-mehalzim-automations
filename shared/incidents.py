"""Shared incident taxonomy used by the summary/report automations.

Single source of truth for how a Monday incident's raw status (the
`status_mkmb1zc6` column) maps to a display label (English or Hebrew) and an
accent color, plus the set of statuses that mean "an event was opened".

Use the helpers to get the legacy-shaped dicts each automation expects:
    INCIDENT_TYPES   raw status -> {"en", "he", "color"}
    labels(lang)     raw status -> label in that language
    colors_by_label(lang)  label in that language -> color
    EVENT_STATUSES   raw statuses that count as an opened/handled event
"""

# raw Monday status (status_mkmb1zc6) -> display labels + accent color
INCIDENT_TYPES = {
    "רפואי":        {"en": "Medical",         "he": "רפואי",       "color": "#e74c3c"},
    "נפשי":         {"en": "Mental Health",   "he": "נפשי",        "color": "#9b59b6"},
    "חילוץ":        {"en": "Rescue",          "he": "חילוץ",        "color": "#e67e22"},
    "איתור":        {"en": "Search & Locate", "he": "איתור",        "color": "#3498db"},
    "אנטישמיות":     {"en": "Antisemitism",    "he": "אנטישמיות",    "color": "#c0392b"},
    "חברות מחלצות":  {"en": "Sexual Assault",  "he": "פגיעה מינית",  "color": "#8e44ad"},
    "אחר":          {"en": "Other",           "he": "אחר",         "color": "#7f8c8d"},
}

# raw statuses (color_mkvvrm1r) that mean an event was opened / handled
EVENT_STATUSES = {"נפתח אירוע", "טופל על ידי רון", "אירוע משמעותי"}


def labels(lang):
    """Map raw status -> label in `lang` ('en' or 'he')."""
    return {raw: v[lang] for raw, v in INCIDENT_TYPES.items()}


def colors_by_label(lang):
    """Map display label (in `lang`) -> accent color."""
    return {v[lang]: v["color"] for v in INCIDENT_TYPES.values()}
