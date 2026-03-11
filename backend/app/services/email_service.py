import os
import logging
import httpx
from fastapi import HTTPException, status

from app.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY")

async def send_summary_email(recipient_email: str, summary_content: str):
    """
    Sends the generated sales summary using the Resend Email API.
    """

    if not RESEND_API_KEY:
        logger.error("RESEND_API_KEY not configured.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email service not configured. Missing RESEND_API_KEY."
        )

    url = "https://api.resend.com/emails"

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "from": "Sales Insight Automator <onboarding@resend.dev>",
        "to": [recipient_email],
        "subject": "Sales Insight Automator: Your Executive Sales Summary",
        "html": f"""
        <h2>Executive Sales Summary</h2>
        <pre style="font-family:monospace">{summary_content}</pre>
        <br/>
        <p>Regards,<br/>Sales Insight Automator</p>
        """
    }

    try:
        logger.info(f"Sending email via Resend to {recipient_email}")

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            logger.error(f"Resend API error: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send email: {response.text}"
            )

        logger.info(f"Email successfully sent to {recipient_email}")

    except Exception as e:
        logger.error(f"Email sending failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {e}"
        )