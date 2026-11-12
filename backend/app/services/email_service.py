import html
import logging
import httpx

from app.config import settings
from app.core.sanitizer import mask_email

logger = logging.getLogger(__name__)


class EmailService:
    """
    Secure server-side email dispatch service using Resend.
    Ensures zero credential leakage to client, never logs OTP values,
    and handles missing configuration safely.
    """

    @staticmethod
    def send_otp_email(to_email: str, otp_code: str) -> bool:
        """
        Dispatches a 6-digit verification code to the recipient email via Resend API.
        Falls back safely if RESEND_API_KEY is not configured (e.g. dev/test mode).
        NEVER logs or exposes the OTP plaintext value in logs.
        """
        api_key = settings.RESEND_API_KEY
        from_email = settings.RESEND_FROM_EMAIL

        masked_recipient = mask_email(to_email)
        if not api_key:
            # Safe development / test mode fallback
            logger.info(  # nosemgrep: python.lang.security.audit.logging.logger-credential-disclosure
                "CONVELINA EmailService: Email provider unconfigured. Simulated email delivery for %s (code masked).",
                masked_recipient,
            )
            return True

        # Production / configured Resend dispatch
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "CONVELINA-Verification-Engine/1.0",
        }

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #faf9f6; margin: 0; padding: 32px 16px; }}
            .card {{ max-width: 520px; margin: 0 auto; background: #ffffff; border: 1px solid #e5e2dc; border-radius: 16px; padding: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.04); }}
            .brand {{ font-size: 18px; font-weight: 700; color: #18181b; margin-bottom: 24px; letter-spacing: -0.5px; }}
            .title {{ font-size: 22px; font-weight: 600; color: #18181b; margin-bottom: 8px; }}
            .desc {{ font-size: 14px; color: #52525b; line-height: 1.5; margin-bottom: 24px; }}
            .code-box {{ background: #faf9f6; border: 1px solid #e5e2dc; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 24px; }}
            .code {{ font-size: 36px; font-weight: 700; letter-spacing: 8px; color: #18181b; font-family: monospace; }}
            .footer {{ font-size: 12px; color: #a1a1aa; border-top: 1px solid #f4f4f5; padding-top: 16px; }}
          </style>
        </head>
        <body>
          <div class="card">
            <div class="brand">CONVELINA</div>
            <div class="title">Verify your email address</div>
            <div class="desc">
              Thank you for registering. Enter the following 6-digit verification code to confirm your email and proceed with your account setup. This code expires in 5 minutes.
            </div>
            <div class="code-box">
              <span class="code">{html.escape(str(otp_code))}</span>
            </div>
            <div class="footer">
              This is an automated security email from CONVELINA. If you did not request this verification code, please ignore this message.
            </div>
          </div>
        </body>
        </html>
        """

        payload = {
            "from": from_email,
            "to": [to_email],
            "subject": "CONVELINA — Your Verification Code",
            "html": html_content,
        }

        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=10.0)
            if response.status_code in (200, 201):
                logger.info("CONVELINA EmailService: Successfully dispatched OTP to %s", masked_recipient)
                return True
            logger.error(
                "CONVELINA EmailService: Resend API HTTP error %s for %s: %s",
                response.status_code,
                masked_recipient,
                response.text[:300],
            )
            return False
        except Exception as e:
            logger.error("CONVELINA EmailService: Unexpected error dispatching email to %s: %s", masked_recipient, e)
            return False
