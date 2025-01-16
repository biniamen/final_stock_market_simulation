# users/utils.py

import requests
from django.conf import settings

def verify_captcha(captcha_response: str) -> bool:
    """
    Verifies the reCAPTCHA response with Google's API.

    Args:
        captcha_response (str): The reCAPTCHA response token from the frontend.

    Returns:
        bool: True if verification succeeds, False otherwise.
    """
    secret_key = settings.RECAPTCHA_SECRET_KEY
    if not secret_key or not captcha_response:
        return False

    data = {
        'secret': secret_key,
        'response': captcha_response
    }
    try:
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = response.json()
        return result.get('success', False)
    except requests.exceptions.RequestException as e:
        # Log the exception as needed
        return False
