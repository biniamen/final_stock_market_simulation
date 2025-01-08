# ethio_stock_simulation/utils.py

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

def send_verification_email(to_email, username, otp):
    """Send OTP to user's email via SendGrid."""
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    subject = "Your Account Verification Code"
    content = f"""
Hello {username},

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

def send_order_notification(to_email, username, action, stock_symbol, quantity, price, new_balance=None):
    """
    Send an order execution notification via SendGrid.
    to_email: recipient's email address
    username: recipient's username
    action: 'Buy' or 'Sell'
    stock_symbol: e.g., 'AAPL'
    quantity: number of shares
    price: execution price
    new_balance: optionally pass updated account balance for user
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
