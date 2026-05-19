import json
import anthropic


def match_departments(volunteer: dict) -> dict:
    client = anthropic.Anthropic()

    prompt = f"""Based on the volunteer registration form below, extract and infer the required fields.
Return ONLY a valid JSON object with no extra explanation.

Form data:
- Name: {volunteer.get('name', '')}
- Background: {volunteer.get('background', '')}
- Location: {volunteer.get('location', '')}
- Military / National Service: {volunteer.get('military', '')}
- Volunteer Interests: {volunteer.get('interests', '')}
- Phone: {volunteer.get('phone', '')}
- Email: {volunteer.get('email', '')}
- Languages: {volunteer.get('languages', '')}
- Social Media: {volunteer.get('linkedin', '')}
- Submitted At: {volunteer.get('created_at', '')}

Return a JSON object with exactly these fields:
{{
  "person": "Name or organization name",
  "summary": "2-3 sentence summary of who they are and what they can contribute",
  "country": "Country extracted or inferred from the location field",
  "city": "City extracted or inferred from the location field",
  "phone": "Phone number as provided",
  "email": "Email address as provided",
  "languages": "Languages they speak",
  "social_media_link": "LinkedIn or other social link as provided",
  "joined_at": "{volunteer.get('created_at', '')}",
  "created_at": "{volunteer.get('created_at', '')}",
  "updated_at": "{volunteer.get('created_at', '')}",
  "region_of_activity": "Inferred region where this volunteer would be most useful (e.g. 'Israel - Center', 'North America', 'Europe', 'International')",
  "fields": ["Pick ONLY from this exact list (use the exact strings): satelites, community, rescue_and_operations, resources_and_partnerships, ccc, government_and_industry_officials, medical, spokesmanship, marketing_and_advocacy, family_and_mental_support, tech, logistics, drones, locating, searching_and_locating, contact_person, languages, intel_gathering, investigations, designer. Infer which apply from the volunteer's background and interests."],
  "skills": ["Pick ONLY from this exact list (use the exact strings): מומחה וואטסאפ, מאתר, אחות, קמבצים, סמבצים, חמליסטים, Human-Computer Interaction, פיתוח ותחזוקת המוצר, מנהלי מוצר, אבטחת מידע, לווינות, מידענות, חקירות מורכבות, UI/UX, ראש צוות תכנות, מאפיין מערכת, ניהול משא ומתן במקרי חטיפה, מפעילי רחפנים, מטיסים, בודק מערכת (QA), יוצרי תוכן, משפיענים, קמן, עובדים סוציאלים, אנשי חבל, חובשים, הטסות מורכבות, מגיש עזרה ראשונה חירום, פרויקט כוכב, פיתוח עסקי, ניהול פרויקטים, פרמדיקים, אנשי טיפול, רפואה משלימה, מפתח/ת תוכנה, Robotics, מהנדס/ת נתונים, אוסינט, פרופיילינג, רופאים מומחים, צלם/ת, עורך/ת וידאו, עורך דין, אריכיטקט מערכת, מפתח (Fullstack), מנהל/ת האקתונים, חילוץ, מענה נפשי בחירום, מיפוי (ויזינט), פסיכולוגים, רופא/ה, פסיכיאטרים, פסיכותרפיסטים, אנשי ים, אורתופד, מדריך צלילה, מנהל/ת מעטפת ארגונית, ניהול משאבי אנוש, פיזיוטרפיסטים, אנשי שטח, טייס, וטרינרים, תכנה/פיתוח. Infer which apply from the volunteer's background and experience."],
  "frts": ["First Respond Teams by continent they could join, choose out of: 'africa', 'asia', 'australia', 'south_and_central_america', 'canada', 'europe', 'usa'"]
}}

Note: the volunteer interests fields will have more detailed mapping added in the future."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else parts[0]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("LLM returned non-JSON response")
        return {}
