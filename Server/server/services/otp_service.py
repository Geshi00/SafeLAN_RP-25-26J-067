import smtplib
import random
from email.message import EmailMessage

class EmailOTPService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.port = 465
        self.sender = "anjulahirimuthugoda@aiesec.net" # YOUR EMAIL
        self.password = "szey tfms prae mbzx"       # YOUR GOOGLE APP PASSWORD

    def send_otp(self, receiver_email):
        otp = f"{random.randint(0, 9999):04d}"
        msg = EmailMessage()
        msg.set_content(f"Your SafeLAN Step-Up MFA code is: {otp}\n\nPlease show these digits one by one to your camera.")
        msg['Subject'] = "🛡️ SafeLAN Security Challenge"
        msg['From'] = self.sender
        msg['To'] = receiver_email

        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.port) as server:
                server.login(self.sender, self.password)
                server.send_message(msg)
            return otp
        except Exception as e:
            print(f"SMTP Error: {e}")
            return None