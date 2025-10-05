import os
import smtplib
import ssl
import time
from email.message import EmailMessage
from typing import Iterable, Optional


class EmailAlertSender:
    """Lightweight email alert sender with per-key cooldown.

    Environment variables (all optional unless noted):
      SMTP_HOST (required to enable)
      SMTP_PORT (default 587)
      SMTP_USER
      SMTP_PASSWORD
      SMTP_STARTTLS (default 'true')
      ALERT_EMAIL_FROM (default: SMTP_USER or 'alerts@example.local')
      ALERT_EMAIL_RECIPIENTS (comma separated list)
      ALERT_EMAIL_COOLDOWN_SECONDS (default 300)
    """
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.starttls = os.getenv('SMTP_STARTTLS', 'true').lower() in ('1','true','yes','on')
        self.from_addr = os.getenv('ALERT_EMAIL_FROM') or self.smtp_user or 'alerts@example.local'
        self.recipients = [r.strip() for r in os.getenv('ALERT_EMAIL_RECIPIENTS','').split(',') if r.strip()]
        self.cooldown = int(os.getenv('ALERT_EMAIL_COOLDOWN_SECONDS','300'))
        self._last_sent: dict[str,float] = {}

    @property
    def enabled(self) -> bool:
        return bool(self.smtp_host and self.recipients)

    def _should_send(self, key: str) -> bool:
        now = time.time()
        last = self._last_sent.get(key, 0)
        if now - last >= self.cooldown:
            self._last_sent[key] = now
            return True
        return False

    def build_message(self, subject: str, body: str, recipients: Optional[Iterable[str]] = None) -> EmailMessage:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = self.from_addr
        rcpts = list(recipients) if recipients else self.recipients
        msg['To'] = ', '.join(rcpts)
        msg.set_content(body)
        return msg

    def send(self, subject: str, body: str, key: str, recipients: Optional[Iterable[str]] = None) -> bool:
        if not self.enabled:
            return False
        if not self._should_send(key):
            return False
        msg = self.build_message(subject, body, recipients)
        context = ssl.create_default_context()
        try:
            if self.starttls:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.ehlo()
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            return True
        except Exception:
            # swallow errors; backend logging will capture via wrapper
            return False
