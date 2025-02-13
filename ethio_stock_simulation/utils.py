import sendgrid
from sendgrid.helpers.mail import Mail
import random
from decouple import config

from ethio_stock_simulation.settings import SENDGRID_API_KEY, SENDGRID_FROM_EMAIL

SENDGRID_API_KEY = config('SENDGRID_API_KEY', default=SENDGRID_API_KEY)
SENDGRID_FROM_EMAIL = config('SENDGRID_FROM_EMAIL', default=SENDGRID_FROM_EMAIL)


def generate_otp():
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))


def send_verification_email(to_email, username, otp, role, company_name=None):
    """
    Send OTP to user's email via SendGrid, including user role and company name (if applicable).
    """
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    subject = "Your Account Verification Code"

    if role == 'company_admin' and company_name:
        content = f"""
Hello {username} ({role}),

Company: {company_name}

Thank you for registering on the Ethiopian Stock Market Simulation Platform.

Your one-time verification code is: {otp}

This code will expire in 10 minutes. If you did not request this, please contact support.

Best regards,

Ethiopian Stock Market Simulation Team
"""
    else:
        content = f"""
Hello {username} ({role}),

Thank you for registering on the Ethiopian Stock Market Simulation Platform.

Your one-time verification code is: {otp}

This code will expire in 10 minutes. If you did not request this, please contact support.

Best regards,

Ethiopian Stock Market Simulation Team
"""

    message = Mail(
        from_email=SENDGRID_FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        plain_text_content=content
    )
    try:
        response = sg.send(message)
        print(f"Email sent to {to_email}. Status Code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_kyc_approved_email(to_email, username):
    """Notify user that their KYC has been approved."""
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    subject = "KYC Approval Notification"
    content = f"""
Hello {username},

Congratulations! Your KYC (Know Your Customer) verification has been successfully approved.

You can now log in and access all features of the Ethiopian Stock Market Simulation Platform.

If you have any questions or need further assistance, please contact our support team.

Best regards,

Ethiopian Stock Market Simulation Team
"""
    message = Mail(
        from_email=SENDGRID_FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        plain_text_content=content
    )
    try:
        response = sg.send(message)
        print(f"KYC approval email sent to {to_email}. Status Code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Failed to send KYC approval email: {e}")
        return False


def send_kyc_rejected_email(to_email, username):
    """Notify user that their KYC has been rejected."""
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    subject = "KYC Rejection Notification"
    content = f"""
Hello {username},

We regret to inform you that your KYC (Know Your Customer) verification has been rejected.

Please review the submitted documents and ensure they meet the required standards. 
You can contact our support team for further assistance or to resubmit your KYC documents.

Best regards,

Ethiopian Stock Market Simulation Team
"""
    message = Mail(
        from_email=SENDGRID_FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        plain_text_content=content
    )
    try:
        response = sg.send(message)
        print(f"KYC rejection email sent to {to_email}. Status Code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Failed to send KYC rejection email: {e}")
        return False


def send_account_kyc_verified_email(to_email, username):
    """Notify user that both their account and KYC have been verified."""
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    subject = "Account and KYC Verification Successful"
    content = f"""
Hello {username},

We are pleased to inform you that your account and KYC verification have been successfully completed.

You now have full access to all features of the Ethiopian Stock Market Simulation Platform. 
Start trading and make the most of our simulation tools!

If you have any questions, feel free to reach out to our support team.

Best regards,

Ethiopian Stock Market Simulation Team
"""
    message = Mail(
        from_email=SENDGRID_FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        plain_text_content=content
    )
    try:
        response = sg.send(message)
        print(f"Account and KYC verified email sent to {to_email}. Status Code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Failed to send account and KYC verified email: {e}")
        return False


def send_order_notification(to_email, username, action, stock_symbol, quantity, price, new_balance=None):
    """
    Send an order execution notification.
    """
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    subject = "Order Execution Notification"
    content = f"""
Hello {username},

We are pleased to inform you that your order has been executed successfully:

    Action: {action}
    Stock: {stock_symbol}
    Quantity: {quantity}
    Execution Price: {float(price):,.2f}

"""
    if new_balance is not None:
        content += f"Your updated account balance is now: {float(new_balance):,.2f}\n\n"

    content += """Thank you for trading with the Ethiopian Stock Market Simulation Platform.

Best regards,
Ethiopian Stock Market Simulation Team
"""

    message = Mail(
        from_email=SENDGRID_FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        plain_text_content=content
    )
    try:
        response = sg.send(message)
        print(f"Order execution email sent to {to_email}. Status Code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
