import secrets
import string
import logging
import re


from odoo.http import request, content_disposition

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
    
    def get_http_headers(self, model, report_type, report, download):
        """Get HTTP headers
        """
        
        headers = {
            'Content-Type': 'application/pdf' if report_type == 'pdf' else 'text/html',
            'Content-Length': len(report),
        }
        
        if report_type == 'pdf' and download:
            filename = "%s.pdf" % (re.sub('\W+', '-', model._get_report_base_filename()))
            headers['Content-Disposition'] = content_disposition(filename)
        return headers
    
    def get_zip_headers(content, filename):
        return [
            ('Content-Type', 'zip'),
            ('X-Content-Type-Options', 'nosniff'),
            ('Content-Length', len(content)),
            ('Content-Disposition', content_disposition(filename)),
        ]