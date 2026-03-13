import os
from twilio.rest import Client
import phonenumbers

def format_phone_number(phone: str, default_country="IN") -> str:
    """
    Cleans and formats phone numbers to E.164 format.
    Automatically handles Indian numbers if default_country='IN'.
    """
    try:
        parsed_number = phonenumbers.parse(str(phone), default_country)
        if phonenumbers.is_valid_number(parsed_number):
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        else:
            print(f"Invalid phone number parsed: {phone}")
            return None
    except Exception as e:
        # Fallback simple cleaner
        clean = ''.join(filter(str.isdigit, str(phone)))
        if len(clean) == 10:
            return f"+91{clean}" # Assume IN
        elif len(clean) > 10:
            return f"+{clean}"
        print(f"Phone parse error for {phone}: {e}")
        return None

def send_sms(to_phone: str, message: str) -> bool:
    """
    Sends an SMS notification using Twilio.
    Includes error handling and automatic phone formatting.
    """
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_phone = os.getenv('TWILIO_PHONE_NUMBER')

    formatted_phone = format_phone_number(to_phone)
    if not formatted_phone:
        print(f"Cannot send SMS. Invalid phone format: {to_phone}")
        return False

    if not account_sid or not auth_token or not from_phone:
        print(f"Mock SMS sent to {formatted_phone}: {message}")
        # Return True for demonstration purposes if keys are absent
        return True

    try:
        client = Client(account_sid, auth_token)
        msg = client.messages.create(
            body=message,
            from_=from_phone,
            to=formatted_phone
        )
        print(f"SMS Sent successfully. SID: {msg.sid}")
        return True
    except Exception as e:
        print(f"Twilio API Error while sending to {formatted_phone}: {e}")
        return False
