from __future__ import annotations

import smtplib
from email.mime.text import MIMEText


def send_selection_email(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    to_email: str,
    candidate_name: str,
) -> bool:
    if not all([smtp_host, smtp_port, smtp_user, smtp_password, to_email]):
        return False

    message = MIMEText(
        f"Hello {candidate_name},\n\nCongratulations! You are selected for the next stage of interview.\nOur team will contact you soon.\n\nRegards,\nAdmin Team"
    )
    message["Subject"] = "Interview Selection Update"
    message["From"] = smtp_user
    message["To"] = to_email

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, [to_email], message.as_string())
        return True
    except Exception:
        return False
