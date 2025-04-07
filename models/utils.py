import secrets
import string
import logging
import re
import json
from werkzeug import urls


from odoo.http import request, content_disposition, route, Response
from odoo.addons.payment import utils as payment_utils
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError, AccessError, AccessDenied, MissingError

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
            filename = "%s.pdf" % (re.sub(r'\W+', '-', model._get_report_base_filename()))
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
            base_url = request.env['ir.config_parameter'].sudo().get_param('naidash_base_url')
            
            if not base_url:
                data = json.dumps(
                    {
                        "error": {
                            "code": 404,
                            "message": "Base URL not found"
                        }
                    }
                )
                
                return request.make_response(data, headers, status=404)
            
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
        
    def send_sms_using_template(self, template_id, record_id, partner_ids):
        """
        Sends an SMS to partner(s).This method works well  
        with templates that have models associated with them
        """
        try:
            wk_sms = request.env["wk.sms.sms"]
            create_sms = wk_sms.create_the_sms(
                {
                    "group_type": "multiple",
                    "template_id": template_id,
                    "record_id": record_id,
                    "partner_ids": partner_ids
                }
            )
            
            sms_id = int(create_sms.get("data").get("id"))
            
            if sms_id:
                sms_response = wk_sms.send_the_sms(sms_id)
                logger.info(f"SMS info:\n\n{sms_response}")
        except MissingError as e:
            logger.error(f"MissingError ocurred while sending the SMS:\n\n{str(e)}")
            msg = _("Record does not exist")
            raise MissingError(msg)
        except UserError as e:
            logger.error(f"UserError ocurred while sending the SMS:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.exception(f"Exception error ocurred while sending the SMS:\n\n{str(e)}")
            raise e
        