import secrets
import string
import logging

logger = logging.getLogger(__name__)

class NaidashUtils:    
    def generate_payment_token(self):
        """Generate a ten-character alphanumeric payment token
        """
        
        letters = string.ascii_uppercase
        digits = string.digits
        first_three_chars = ''.join(secrets.choice(letters) for _ in range(3))
        fourth_char = secrets.choice(digits)
        remaining_chars = ''.join(secrets.choice(letters + digits) for _ in range(6))
        payment_token = first_three_chars + fourth_char + remaining_chars
        
        return payment_token

