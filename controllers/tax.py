# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, route, SessionExpiredException
from odoo.service import security
from odoo.service.security import check_session

logger = logging.getLogger(__name__)

class NaidashTax(http.Controller):
    @route('/api/v1/naidash/tax', methods=['POST'], auth='user', type='json')
    def create_tax(self, **kw):
        """Create the tax details
        """ 

        try:            
            request_data = json.loads(request.httprequest.data)                        
            tax_details = request.env['account.tax'].create_the_tax(request_data)
            return tax_details
        except TypeError as e:
            logger.error(f"This datatype error ocurred while modifying the tax details:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }         
        except Exception as e:
            logger.exception(f"The following error occurred while creating the tax details:\n\n{str(e)}")
            return {
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/tax/<int:tax_id>', methods=['PATCH'], auth='user', type='json')
    def edit_tax(self, tax_id, **kw):
        """Edit the tax details
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            tax_details = request.env['account.tax'].edit_the_tax(tax_id, request_data)
            return tax_details
        except TypeError as e:
            logger.error(f"This datatype error ocurred while modifying the tax details:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }        
        except Exception as e:
            logger.exception(f"This error occurred while modifying the tax details:\n\n{str(e)}")
            return {            
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/tax/<int:tax_id>', methods=['GET'], auth='user', type='http')
    def get_tax(self, tax_id):
        """Get the tax details
        """ 
                
        headers = [('Content-Type', 'application/json')]
        
        try:
            tax_details = request.env['account.tax'].get_the_tax(tax_id)
            status_code = tax_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": tax_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": tax_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the tax details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/naidash/tax', methods=['GET'], auth='user', type='http')
    def get_taxes(self):
        """
        Gets all the taxes
        """ 
        
        headers = [
            ('Content-Type', 'application/json')
        ]
                
        try:
            tax_details = request.env['account.tax'].get_all_the_taxes()
            status_code = tax_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": tax_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:                
                data = json.dumps(
                    {
                        "result": tax_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the taxes:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)}
                }
            )
            
            return request.make_response(data, headers, status=500)
            