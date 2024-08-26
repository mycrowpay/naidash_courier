# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, route, SessionExpiredException
from odoo.service import security
from odoo.service.security import check_session

logger = logging.getLogger(__name__)

class NaidashDimensionPrice(http.Controller):
    @route('/api/v1/naidash/dimension_price', methods=['POST'], auth='user', type='json')
    def create_dimension_price(self, **kw):
        """Create the dimension price details
        """ 

        try:            
            request_data = json.loads(request.httprequest.data)                        
            dimension_price_details = request.env['dimension.price.custom'].create_the_dimension_price(request_data)
            return dimension_price_details
        except Exception as e:
            logger.exception(f"The following error occurred while creating the dimension price details:\n\n{str(e)}")
            return {
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/dimension_price/<int:dimension_price_id>', methods=['PATCH'], auth='user', type='json')
    def edit_dimension_price(self, dimension_price_id, **kw):
        """Edit the dimension price details
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            dimension_price_details = request.env['dimension.price.custom'].edit_the_dimension_price(dimension_price_id, request_data)
            return dimension_price_details
        except TypeError as e:
            logger.error(f"This datatype error ocurred while modifying the dimension price details:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }        
        except Exception as e:
            logger.exception(f"This error occurred while modifying the dimension price details:\n\n{str(e)}")
            return {            
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/dimension_price/<int:dimension_price_id>', methods=['GET'], auth='user', type='http')
    def get_dimension_price(self, dimension_price_id):
        """Get the dimension price details
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:
            dimension_price_details = request.env['dimension.price.custom'].get_the_dimension_price(dimension_price_id)
            status_code = dimension_price_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": dimension_price_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": dimension_price_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the dimension price details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/naidash/dimension_price', methods=['GET'], auth='user', type='http')
    def get_dimension_prices(self):
        """
        Returns all the dimension prices
        """ 
        
        headers = [
            ('Content-Type', 'application/json')
        ]
                
        try:
            dimension_price_details = request.env['dimension.price.custom'].get_all_the_dimension_prices()
            status_code = dimension_price_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": dimension_price_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:                
                data = json.dumps(
                    {
                        "result": dimension_price_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the dimension prices:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)}
                }
            )
            
            return request.make_response(data, headers, status=500)
            