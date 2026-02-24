"""Email Service for sending emails via Mailtrap"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import httpx for API-based sending
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

# SMTP imports (always available)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailService:
    """Service for sending emails via Mailtrap (API or SMTP)"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_host: Optional[str] = None,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None
    ):
        """
        Initialize EmailService with Mailtrap credentials.
        
        Supports two modes:
        1. API Mode (Mailtrap Email Sending): Uses REST API
        2. SMTP Mode (Mailtrap Email Testing): Uses SMTP
        
        Environment variables:
        - MAILTRAP_API_KEY: API key for Email Sending
        - MAILTRAP_API_HOST: API host (default: send.api.mailtrap.io)
        - MAILTRAP_SMTP_HOST: SMTP host (default: smtp.mailtrap.io)
        - MAILTRAP_SMTP_PORT: SMTP port (default: 587)
        - MAILTRAP_USERNAME: SMTP username
        - MAILTRAP_PASSWORD: SMTP password/API key
        - MAILTRAP_FROM_EMAIL: Default from email address
        """
        # API configuration (for Email Sending)
        self.api_key = api_key or os.getenv("MAILTRAP_API_KEY")
        self.api_host = api_host or os.getenv("MAILTRAP_API_HOST", "send.api.mailtrap.io")
        
        # SMTP configuration (for Email Testing)
        self.smtp_host = smtp_host or os.getenv("MAILTRAP_SMTP_HOST", "smtp.mailtrap.io")
        self.smtp_port = smtp_port or int(os.getenv("MAILTRAP_SMTP_PORT", "587"))
        self.smtp_username = smtp_username or os.getenv("MAILTRAP_USERNAME")
        self.smtp_password = smtp_password or os.getenv("MAILTRAP_PASSWORD")
        
        self.from_email = from_email or os.getenv("MAILTRAP_FROM_EMAIL", "noreply@crm.com")

        # Determine which mode to use
        self.use_api = bool(self.api_key) and HTTPX_AVAILABLE
        self.use_smtp = bool(self.smtp_username and self.smtp_password) and not self.use_api
        self._is_configured = self.use_api or self.use_smtp
        
        logger.debug(f"EmailService initialized: use_api={self.use_api}, use_smtp={self.use_smtp}")

    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return self._is_configured

    def get_mode(self) -> str:
        """Get the current sending mode"""
        if self.use_api:
            return "API (Email Sending)"
        elif self.use_smtp:
            return "SMTP (Email Testing)"
        else:
            return "Not configured"

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        html: bool = False,
        cc: Optional[str] = None,
        bcc: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send an email via Mailtrap (API or SMTP)"""
        if not self._is_configured:
            return {
                "success": False,
                "message": "Email service not configured. Please set MAILTRAP_API_KEY or MAILTRAP_USERNAME/MAILTRAP_PASSWORD.",
                "error": "Not configured"
            }

        sender_email = from_email or self.from_email

        if self.use_api:
            return self._send_via_api(to_email, subject, body, sender_email, html, cc, bcc)
        elif self.use_smtp:
            return self._send_via_smtp(to_email, subject, body, sender_email, html, cc, bcc)
        else:
            return {
                "success": False,
                "message": "No sending method available",
                "error": "Neither API nor SMTP configured"
            }

    def _send_via_api(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str,
        html: bool = False,
        cc: Optional[str] = None,
        bcc: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email via Mailtrap API"""
        if not HTTPX_AVAILABLE:
            return {
                "success": False,
                "message": "httpx library not installed. Please install it: pip install httpx",
                "error": "httpx not available"
            }

        try:
            url = f"https://{self.api_host}/api/send"
            
            payload = {
                "from": {"email": from_email},
                "to": [{"email": to_email}],
                "subject": subject,
            }
            
            if html:
                payload["html"] = body
            else:
                payload["text"] = body
            
            if cc:
                payload["cc"] = [{"email": email.strip()} for email in cc.split(",")]
            
            if bcc:
                payload["bcc"] = [{"email": email.strip()} for email in bcc.split(",")]

            logger.debug(f"Sending via API to {url}")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            with httpx.Client() as client:
                response = client.post(url, json=payload, headers=headers, timeout=30.0)
                response.raise_for_status()
            
            logger.debug("Email sent successfully via API!")
            
            return {
                "success": True,
                "message": f"Email sent successfully to {to_email}",
                "sent_at": datetime.now().isoformat(),
                "to": to_email,
                "subject": subject,
                "method": "API"
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Status Error: {e}")
            error_detail = e.response.text if hasattr(e, 'response') else str(e)
            return {
                "success": False,
                "message": f"API request failed: {e.response.status_code}",
                "error": error_detail,
                "error_type": "http_status"
            }
        except httpx.ConnectError as e:
            logger.error(f"Connection Error: {e}")
            return {
                "success": False,
                "message": f"Failed to connect to API: {self.api_host}",
                "error": str(e),
                "error_type": "connection"
            }
        except Exception as e:
            logger.error(f"API Error: {e}")
            return {
                "success": False,
                "message": "Failed to send email via API",
                "error": str(e),
                "error_type": "api"
            }

    def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str,
        html: bool = False,
        cc: Optional[str] = None,
        bcc: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email via SMTP"""
        try:
            logger.debug(f"Connecting to SMTP: {self.smtp_host}:{self.smtp_port}")
            logger.debug(f"Username: {self.smtp_username}")
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_email
            msg["To"] = to_email

            if cc:
                msg["Cc"] = cc

            # Attach body
            content_type = "html" if html else "plain"
            msg.attach(MIMEText(body, content_type))

            # Build recipient list
            recipients = [to_email]
            if cc:
                recipients.extend([email.strip() for email in cc.split(",")])
            if bcc:
                recipients.extend([email.strip() for email in bcc.split(",")])

            # Connect and send
            logger.debug("Establishing SMTP connection...")
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.set_debuglevel(1)
                logger.debug("Starting TLS...")
                server.starttls()
                logger.debug(f"Logging in as {self.smtp_username}...")
                server.login(self.smtp_username, self.smtp_password)
                logger.debug(f"Sending email from {from_email} to {recipients}...")
                server.sendmail(from_email, recipients, msg.as_string())
                logger.debug("Email sent successfully via SMTP!")

            return {
                "success": True,
                "message": f"Email sent successfully to {to_email}",
                "sent_at": datetime.now().isoformat(),
                "to": to_email,
                "subject": subject,
                "method": "SMTP"
            }

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication Error: {e}")
            return {
                "success": False,
                "message": "SMTP Authentication failed. Please check your credentials.",
                "error": str(e),
                "error_type": "authentication"
            }
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP Connection Error: {e}")
            return {
                "success": False,
                "message": f"Failed to connect to SMTP server: {self.smtp_host}:{self.smtp_port}",
                "error": str(e),
                "error_type": "connection"
            }
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"SMTP Server Disconnected: {e}")
            return {
                "success": False,
                "message": "SMTP server disconnected unexpectedly.",
                "error": str(e),
                "error_type": "disconnected"
            }
        except smtplib.SMTPException as e:
            logger.error(f"SMTP Exception: {e}")
            return {
                "success": False,
                "message": "Failed to send email",
                "error": str(e),
                "error_type": "smtp"
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "message": "Unexpected error occurred",
                "error": str(e),
                "error_type": "unknown"
            }

    def test_connection(self) -> Dict[str, Any]:
        """Test the connection"""
        if not self._is_configured:
            return {
                "success": False,
                "message": "Email service not configured"
            }

        if self.use_api:
            # For API, we can't really test without sending, so just verify credentials
            return {
                "success": True,
                "message": "API configuration looks correct. Try sending a test email!",
                "mode": "API",
                "api_host": self.api_host
            }
        elif self.use_smtp:
            try:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                return {
                    "success": True,
                    "message": "Connection successful!",
                    "mode": "SMTP",
                    "smtp_host": self.smtp_host,
                    "smtp_port": self.smtp_port
                }
            except smtplib.SMTPAuthenticationError as e:
                return {
                    "success": False,
                    "message": "Authentication failed. Check your credentials.",
                    "error": str(e)
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Connection failed: {str(e)}",
                    "error": str(e)
                }
        else:
            return {
                "success": False,
                "message": "No sending method configured"
            }


# Global email service instance
email_service = EmailService()


def get_email_service() -> EmailService:
    """Get the global email service instance"""
    return email_service


def send_test_email(to_email: str) -> Dict[str, Any]:
    """Send a test email to verify configuration"""
    service = get_email_service()
    return service.send_email(
        to_email=to_email,
        subject="🧪 Test Email from CRM",
        body="""
        <html>
        <body>
            <h2>✅ Email Service Test Successful!</h2>
            <p>This is a test email from your CRM system.</p>
            <p>If you received this, your Mailtrap integration is working correctly.</p>
            <br>
            <p><strong>Sent at:</strong> {timestamp}</p>
            <p><strong>Mode:</strong> {mode}</p>
        </body>
        </html>
        """.format(timestamp=datetime.now().isoformat(), mode=service.get_mode()),
        html=True
    )
