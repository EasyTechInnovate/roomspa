from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ssl
import smtplib
import os
from pathlib import Path
from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

class EmailProvider:
    def __init__(self, host, port, username, password, use_ssl=True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl

    def send_email(self, sender, recipient, subject, html_content):
        message = MIMEMultipart()
        message['From'] = sender
        message['To'] = recipient
        message['Subject'] = subject
        message.attach(MIMEText(html_content, "html"))
        email_string = message.as_string()

        if self.use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.host, self.port, context=context) as server:
                server.login(self.username, self.password)
                server.sendmail(sender, recipient, email_string)
        else:
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(sender, recipient, email_string)

        return {"success": True}


def get_email_provider():
    return EmailProvider(
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        username=settings.EMAIL_SENDER,
        password=settings.EMAIL_PASSWORD,
        use_ssl=getattr(settings, 'EMAIL_USE_SSL', True)
    )


def load_template(template_name):
    current_dir = Path(__file__).parent
    template_path = current_dir / 'emails' / template_name
    
    with open(template_path, 'r') as file:
        return file.read()


def render_template(template_content, context):
    for key, value in context.items():
        template_content = template_content.replace(f"{{{{ {key} }}}}", str(value))
    return template_content


def send_registration_link(username, email_receiver, registration_link, email_type):
    template_map = {
        "registration": {
            "template": "registration.html",
            "subject": "RoomSpa Account Registration"
        },
        "password_reset": {
            "template": "password_reset.html",
            "subject": "RoomSpa Password Reset"
        },
        "email_update": {
            "template": "email_update.html",
            "subject": "RoomSpa Confirm Your New Email Address"
        }
    }
    
    if email_type not in template_map:
        return {"success": False, "error": f"Unknown email type: {email_type}"}
    
    template_data = template_map[email_type]
    
    context = {
        "username": username,
        "registration_link": registration_link
    }
    
    template_content = load_template(template_data["template"])
    html_content = render_template(template_content, context)
    subject = template_data["subject"]
    
    email_provider = get_email_provider()
    return email_provider.send_email(
        sender=settings.EMAIL_SENDER,
        recipient=email_receiver,
        subject=subject,
        html_content=html_content
    )


# =================== SMS OTP FUNCTIONS ===================

def get_twilio_client():
    """Initialize Twilio client with credentials from settings"""
    try:
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        return Client(account_sid, auth_token)
    except Exception as e:
        print(f"Error initializing Twilio client: {e}")
        return None


def send_sms_otp(phone_number, otp_code, message_type='registration'):
    """Send SMS OTP using Twilio"""
    try:
        client = get_twilio_client()
        if not client:
            return {"success": False, "error": "Twilio client not configured"}

        # Message templates for different types
        message_templates = {
            'registration': f"Your RoomSpa verification code is: {otp_code}. Do not share this code with anyone.",
            'password_reset': f"Your RoomSpa password reset code is: {otp_code}. Do not share this code with anyone.",
            'login': f"Your RoomSpa login verification code is: {otp_code}. Do not share this code with anyone."
        }

        message_body = message_templates.get(message_type, message_templates['registration'])

        # Send SMS
        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )

        return {
            "success": True,
            "message_sid": message.sid,
            "status": message.status
        }

    except TwilioException as e:
        return {
            "success": False,
            "error": f"Twilio error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"SMS sending failed: {str(e)}"
        }


def verify_phone_format(phone_number):
    """Ensure phone number is in E.164 format for Twilio"""
    if not phone_number:
        return None

    # Remove any spaces, dashes, parentheses
    clean_number = ''.join(filter(str.isdigit, phone_number))

    # Add + if not present and number doesn't start with country code
    if not phone_number.startswith('+'):
        # Assume US number if 10 digits, otherwise add +
        if len(clean_number) == 10:
            return f"+1{clean_number}"
        else:
            return f"+{clean_number}"

    return phone_number


def send_phone_verification(name, phone_number, otp_code, verification_type='registration'):
    """Main function to send phone verification - replaces email function for phone"""
    try:
        # Format phone number for Twilio
        formatted_phone = verify_phone_format(phone_number)

        if not formatted_phone:
            return {"success": False, "error": "Invalid phone number format"}

        # Send SMS
        result = send_sms_otp(formatted_phone, otp_code, verification_type)

        if result["success"]:
            return {
                "success": True,
                "message": f"Verification code sent to {formatted_phone}",
                "message_sid": result.get("message_sid")
            }
        else:
            return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Phone verification failed: {str(e)}"
        }