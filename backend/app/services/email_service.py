import os
import smtplib
import logging
from email.mime.text import MIMEText
from fastapi import HTTPException, status

from app.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

async def send_summary_email(recipient_email: str, summary_content: str):

    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not all([smtp_server, smtp_port, smtp_username, smtp_password]):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SMTP not configured"
        )

    msg = MIMEText(summary_content)
    msg["Subject"] = "Sales Insight Automator: Executive Summary"
    msg["From"] = smtp_username
    msg["To"] = recipient_email

    try:
        logger.info(f"Sending email to {recipient_email}")

        with smtplib.SMTP(smtp_server, smtp_port, timeout=20) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        logger.info("Email sent successfully")

    except Exception as e:
        logger.error(f"Email sending failed: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {e}"
        )