# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, route, SessionExpiredException
from odoo.service import security
from odoo.service.security import check_session

logger = logging.getLogger(__name__)

class NaidashWeightPrice(http.Controller):
    @route('/api/v1/naidash/weight_price', methods=['POST'], auth='user', type='json')
    def create_weight_price(self, **kw):
        """Create the weight price details
        """ 

        try:            
            request_data = json.loads(request.httprequest.data)                        
            weight_price_details = request.env['weight.price.custom'].create_the_weight_price(request_data)
            return weight_price_details
        except Exception as e:
            logger.exception(f"The following error occurred while creating the weight price details:\n\n{str(e)}")
            return {
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/weight_price/<int:weight_price_id>', methods=['PATCH'], auth='user', type='json')
    def edit_weight_price(self, weight_price_id, **kw):
        """Edit the weight price details
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            weight_price_details = request.env['weight.price.custom'].edit_the_weight_price(weight_price_id, request_data)
            return weight_price_details
        except TypeError as e:
            logger.error(f"This datatype error ocurred while modifying the weight price details:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }        
        except Exception as e:
            logger.exception(f"This error occurred while modifying the weight price details:\n\n{str(e)}")
            return {            
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/weight_price/<int:weight_price_id>', methods=['GET'], auth='user', type='http')
    def get_weight_price(self, weight_price_id):
        """Get the weight price details
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:
            weight_price_details = request.env['weight.price.custom'].get_the_weight_price(weight_price_id)
            status_code = weight_price_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": weight_price_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": weight_price_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the weight price details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/naidash/weight_price', methods=['GET'], auth='user', type='http')
    def get_weight_prices(self):
        """
        Returns all the weight prices
        """ 
        
        headers = [
            ('Content-Type', 'application/json')
        ]
                
        try:
            weight_price_details = request.env['weight.price.custom'].get_all_the_weight_prices()
            status_code = weight_price_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": weight_price_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:                
                data = json.dumps(
                    {
                        "result": weight_price_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the weight prices:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)}
                }
            )
            
            return request.make_response(data, headers, status=500)
            