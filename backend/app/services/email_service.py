
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from fastapi import HTTPException, status

from app.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

async def send_summary_email(recipient_email: str, summary_content: str):
    """
    Sends the generated sales summary via email using SMTP.
    """
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    if not all([smtp_username, smtp_password, smtp_server, smtp_port]):
        logger.error("SMTP environment variables not fully configured.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email service not configured. Missing SMTP credentials."
        )

    msg = MIMEMultipart("alternative")
    msg['Subject'] = "Sales Insight Automator: Your Executive Sales Summary"
    msg['From'] = smtp_username
    msg['To'] = recipient_email

    # Create the plain-text and HTML versions of your message
    text = f"Dear Recipient,\n\nPlease find your executive sales summary below:\n\n{summary_content}\n\nBest regards,\nSales Insight Automator Team"
    html = f"""
    <html>
        <body>
            <p>Dear Recipient,</p>
            <p>Please find your executive sales summary below:</p>
            <pre>{summary_content}</pre>
            <p>Best regards,<br>
            Sales Insight Automator Team</p>
        </body>
    </html>
    """

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    msg.attach(part1)
    msg.attach(part2)

    try:
        logger.info(f"Attempting to send email from {smtp_username} to {recipient_email} via {smtp_server}:{smtp_port}")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_username, recipient_email, msg.as_string())
        logger.info(f"Email successfully sent to {recipient_email}")
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed. Check username and password.", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate with email server. Check SMTP username and password."
        )
    except smtplib.SMTPConnectError:
        logger.error(f"SMTP connection failed to {smtp_server}:{smtp_port}.", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect to SMTP server {smtp_server}:{smtp_port}."
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending email to {recipient_email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {e}"
        )
