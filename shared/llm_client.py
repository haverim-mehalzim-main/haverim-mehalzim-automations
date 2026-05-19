import json
import anthropic

_client = anthropic.Anthropic()


def match_departments(volunteer: dict) -> dict:
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
  "fields": ["Departments/categories they can contribute to — 'ccc' means Central Control Center. Infer from interests and background."],
  "skills": ["Concrete skills based on their background, military service, and stated interests"],
  "frts": ["First Respond Teams by continent they could join, e.g. 'FRT-Israel', 'FRT-Europe', 'FRT-North America', 'FRT-South America', 'FRT-Asia'"]
}}

Note: the volunteer interests fields will have more detailed mapping added in the future."""

    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"LLM returned non-JSON response: {raw}")
        return {}
