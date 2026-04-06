"""
Email service for sending notifications.

Provides async email sending functionality with SMTP support.
Gracefully handles SMTP disabled mode for development.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


async def send_invitation_email(
    to_email: str,
    invited_by: str,
    org_name: str,
    role: str,
    token: str,
) -> None:
    """Send an invitation email to join an organisation.

    This function is fire-and-forget - email failures never fail the API call.
    If SMTP is disabled (smtp_host is empty or "disabled"), the invite URL
    is logged instead of sending an email.

    Args:
        to_email: Recipient email address
        invited_by: Name or email of the person who sent the invitation
        org_name: Name of the organisation
        role: Role being offered (auditor, reviewer, viewer)
        token: Unique invitation token for the accept URL
    """
    invite_url = f"{settings.frontend_url}/invitations/{token}"

    # Check if SMTP is disabled
    if not settings.smtp_host or settings.smtp_host.lower() == "disabled":
        # Print to stdout so it appears in docker logs
        print(f"\n{'='*60}")
        print(f"INVITATION EMAIL (SMTP DISABLED)")
        print(f"{'='*60}")
        print(f"To: {to_email}")
        print(f"Organisation: {org_name}")
        print(f"Role: {role}")
        print(f"Invited by: {invited_by}")
        print(f"\n INVITATION URL:")
        print(f"{invite_url}")
        print(f"{'='*60}\n")

        logger.info(
            "email_smtp_disabled",
            to_email=to_email,
            org_name=org_name,
            role=role,
            invite_url=invite_url,
            message="SMTP disabled - invitation URL logged instead of email",
        )
        return

    subject = f"You've been invited to join {org_name} on A11y Platform"

    # Plain text body
    body = f"""Hi,

{invited_by} has invited you to join {org_name} on the A11y Accessibility Evaluation Platform.

You've been invited as: {role.title()}

To accept this invitation, click the link below:
{invite_url}

This invitation will expire in 7 days.

If you didn't expect this invitation, you can safely ignore this email.

---
A11y Platform - WCAG Accessibility Evaluation
"""

    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from
        msg["To"] = to_email

        # Attach plain text part
        text_part = MIMEText(body, "plain", "utf-8")
        msg.attach(text_part)

        # HTML version
        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 24px;">You're Invited!</h1>
    </div>
    <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
        <p style="margin-top: 0;"><strong>{invited_by}</strong> has invited you to join <strong>{org_name}</strong> on the A11y Accessibility Evaluation Platform.</p>

        <p>You've been invited as: <strong style="color: #667eea;">{role.title()}</strong></p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{invite_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Accept Invitation</a>
        </div>

        <p style="color: #666; font-size: 14px;">This invitation will expire in 7 days.</p>

        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;">

        <p style="color: #999; font-size: 12px; margin-bottom: 0;">If you didn't expect this invitation, you can safely ignore this email.</p>
    </div>
    <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
        A11y Platform - WCAG Accessibility Evaluation
    </div>
</body>
</html>"""

        html_part = MIMEText(html_body, "html", "utf-8")
        msg.attach(html_part)

        # Send email
        if settings.smtp_port == 465:
            # SSL connection
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_from, to_email, msg.as_string())
        else:
            # STARTTLS connection (port 587 or other)
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_from, to_email, msg.as_string())

        logger.info(
            "email_sent",
            to_email=to_email,
            org_name=org_name,
            subject=subject,
        )

    except Exception as e:
        # Email failure should never fail the API call
        logger.error(
            "email_send_failed",
            to_email=to_email,
            org_name=org_name,
            error=str(e),
            invite_url=invite_url,
            message="Email send failed - invitation URL logged for manual follow-up",
        )
