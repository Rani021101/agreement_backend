from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import os

RECEIVER_EMAIL= os.getenv("RECEIVER_EMAIL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_KEY=os.getenv("APP_KEY")

def send_email(to_email, subject, html_body):
    print("sender email", SENDER_EMAIL)
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, APP_KEY)
            server.send_message(msg)
    except Exception as e:
        print(e)

def create_reminder_email(building_name, renewal_date, days_left):

    return f"""
    <html>
    <body style="font-family:Arial;background:#f5f7fa;padding:20px;">

        <div style="
            max-width:650px;
            margin:auto;
            background:white;
            border-radius:10px;
            overflow:hidden;
            border:1px solid #ddd;
        ">

            <div style="
                background:#2563eb;
                color:white;
                padding:20px;
                text-align:center;
            ">
                <h2>Agreement Renewal Reminder</h2>
            </div>

            <div style="padding:25px;">

                <p>Hello,</p>

                <p>
                    Your agreement is due for renewal in
                    <strong>{days_left} day(s)</strong>.
                </p>

                <table
                    style="
                        width:100%;
                        border-collapse:collapse;
                        margin-top:15px;
                    "
                >
                    <tr>
                        <td style="padding:10px;border:1px solid #ddd;">
                            Building Name
                        </td>
                        <td style="padding:10px;border:1px solid #ddd;">
                            {building_name}
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:10px;border:1px solid #ddd;">
                            Renewal Date
                        </td>
                        <td style="padding:10px;border:1px solid #ddd;">
                            {renewal_date}
                        </td>
                    </tr>
                </table>

                <p style="
                    margin-top:20px;
                    color:#dc2626;
                    font-weight:bold;
                ">
                    Please complete the renewal process before the expiry date.
                </p>

            </div>

            <div style="
                background:#f3f4f6;
                padding:15px;
                text-align:center;
                font-size:12px;
            ">
                Automated Reminder - Agreement Management Portal
            </div>

        </div>

    </body>
    </html>
    """



