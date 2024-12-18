import secrets
import string
import logging
import re
import json
from werkzeug import urls


from odoo.http import request, content_disposition, route, Response
from odoo.addons.payment import utils as payment_utils

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
                        
    def generate_payment_link(self, partner_id, amount, currency_id, transaction_ref):
        headers = [('Content-Type', 'application/json')]
        
        try:
            base_url = request.env['ir.config_parameter'].sudo().get_param('app_1_base_url')
            
            if not base_url:
                data = json.dumps(
                    {
                        "error": {
                            "code": 500,
                            "message": "Base URL not found"
                        }
                    }
                )
                
                return request.make_response(data, headers, status=500)
            
            # Generate an access token based on the provided values
            access_token = payment_utils.generate_access_token(
                partner_id, amount, currency_id, transaction_ref
            )
            
            url_params = {
                'token': access_token
            }
            
            payment_link = f'{base_url}/payment?{urls.url_encode(url_params)}'
            
            # Save the payment link
            partner = request.env['res.partner'].browse(int(partner_id))
            partner.write({"payment_url": payment_link})
            
            return payment_link
        except Exception as e:
            logger.exception(f"The following error occurred while generating the payment link:\n\n{str(e)}")
            raise e
        
    def verify_payment_token(self, access_token, partner_id, amount, currency_id, transaction_ref):        
        try:           
            # Check the validity of the access token for the provided values 
            is_valid_token = payment_utils.check_access_token(
                access_token, partner_id, amount, currency_id, transaction_ref
            )
            
            return is_valid_token
        except Exception as e:
            logger.exception(f"The following error occurred while verifying the payment token:\n\n{str(e)}")
            raise e