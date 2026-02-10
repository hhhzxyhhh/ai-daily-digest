from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(
    smtp_host: str,
    smtp_port: int,
    sender: str,
    password: str,
    recipients: list[str],
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    if html_body:
        msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipients, msg.as_string())
