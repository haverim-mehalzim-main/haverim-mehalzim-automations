import os
import anthropic

_client = anthropic.Anthropic()


def match_departments(volunteer_data: dict) -> str:
    # TODO: replace with actual prompt when provided
    prompt = f"TODO: prompt will be provided.\n\nVolunteer data:\n{volunteer_data}"

    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
