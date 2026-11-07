"""Mail the YouTube upload report through Instagram repo's existing SMTP secrets."""
import os
import re
import smtplib
import ssl
from email.message import EmailMessage


def main():
    video_id = os.environ.get("VIDEO_ID", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("Geçersiz YouTube video kimliği; rapor gönderilmedi")
    title = " ".join(os.environ.get("VIDEO_TITLE", "").split())[:180]
    date = os.environ.get("VIDEO_DATE", "")
    if not re.fullmatch(r"\\d{4}-\\d{2}-\\d{2}", date):
        date = "Tarih doğrulanamadı"
    privacy = os.environ.get("VIDEO_PRIVACY", "").strip().lower()
    if privacy not in {"public", "unlisted", "private"}:
        privacy = "bilinmiyor"

    user = os.environ.get("SMTP_USER", "").strip()
    password = "".join(os.environ.get("SMTP_PASS", "").split())
    recipient = (os.environ.get("MAIL_TO") or user).strip()
    if not user or not password or not recipient:
        raise RuntimeError("Instagram deposunun SMTP_USER, SMTP_PASS veya MAIL_TO ayarları eksik.")

    msg = EmailMessage()
    msg["Subject"] = f"BotZayba YouTube videosu | {date} | {title}"
    msg["From"] = user
    msg["To"] = recipient
    msg.set_content(
        f"Günlük YouTube videosu başarıyla yüklendi.\\n\\n"
        f"Tarih: {date}\\nBaşlık: {title}\\nGörünürlük: {privacy}\\n"
        f"Video: https://www.youtube.com/shorts/{video_id}\\n\\n"
        "Bu e-posta GitHub'daki botzayba-instagram otomasyonundan gönderildi.\\n"
    )
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=45, context=ssl.create_default_context()) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
    print("YouTube video raporu e-postası gönderildi:", video_id)


if __name__ == "__main__":
    main()
