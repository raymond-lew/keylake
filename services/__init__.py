"""Services package for CRM"""

from .email_service import EmailService, get_email_service, send_test_email

__all__ = ["EmailService", "get_email_service", "send_test_email"]
