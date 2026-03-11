import os
import httpx
from fastapi import HTTPException, status

BREVO_API_KEY = os.getenv("BREVO_API_KEY")

async def send_summary_email(recipient_email: str, summary_content: str):

    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    payload = {
        "sender": {
            "name": "Sales Insight Automator",
            "email": "poudelsamundra162@gmail.com"
        },
        "to": [
            {"email": recipient_email}
        ],
        "subject": "Sales Insight Automator: Executive Sales Summary",
        "htmlContent": f"<pre>{summary_content}</pre>"
    }

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(url, headers=headers, json=payload)

    if r.status_code not in [200, 201]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {r.text}"
        )