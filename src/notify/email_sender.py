"""Envío del email vía SMTP (compatible con Gmail, Outlook, etc.)."""
from __future__ import annotations
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(subject: str, html_body: str) -> None:
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASS"]
    mail_to = os.getenv("MAIL_TO", user)
    mail_from = os.getenv("MAIL_FROM", user)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = mail_to

    msg.attach(MIMEText("Tu cliente no soporta HTML. Abrí la versión web.", "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(mail_from, [addr.strip() for addr in mail_to.split(",")], msg.as_string())
    print(f"[Email] Enviado a {mail_to}")
