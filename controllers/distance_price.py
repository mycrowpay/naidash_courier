# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, route, SessionExpiredException
from odoo.service import security
from odoo.service.security import check_session

logger = logging.getLogger(__name__)

class NaidashDistancePrice(http.Controller):
    @route('/api/v1/naidash/distance_price', methods=['POST'], auth='user', type='json')
    def create_distance_price(self, **kw):
        """Create the distance price details
        """ 

        try:            
            request_data = json.loads(request.httprequest.data)                        
            distance_price_details = request.env['distance.price.custom'].create_the_distance_price(request_data)
            return distance_price_details
        except Exception as e:
            logger.exception(f"The following error occurred while creating the distance price details:\n\n{str(e)}")
            return {
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/distance_price/<int:distance_price_id>', methods=['PATCH'], auth='user', type='json')
    def edit_distance_price(self, distance_price_id, **kw):
        """Edit the distance price details
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            distance_price_details = request.env['distance.price.custom'].edit_the_distance_price(distance_price_id, request_data)
            return distance_price_details
        except TypeError as e:
            logger.error(f"This datatype error ocurred while modifying the distance price details:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }        
        except Exception as e:
            logger.exception(f"This error occurred while modifying the distance price details:\n\n{str(e)}")
            return {            
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/distance_price/<int:distance_price_id>', methods=['GET'], auth='user', type='http')
    def get_distance_price(self, distance_price_id):
        """Get the distance price details
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:
            distance_price_details = request.env['distance.price.custom'].get_the_distance_price(distance_price_id)
            status_code = distance_price_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": distance_price_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": distance_price_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the distance price details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/naidash/distance_price', methods=['GET'], auth='user', type='http')
    def get_distance_prices(self):
        """
        Returns all the distance prices
        """ 
        
        headers = [
            ('Content-Type', 'application/json')
        ]
                
        try:
            distance_price_details = request.env['distance.price.custom'].get_all_the_distance_prices()
            status_code = distance_price_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": distance_price_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:                
                data = json.dumps(
                    {
                        "result": distance_price_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the distance prices:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)}
                }
            )
            
            return request.make_response(data, headers, status=500)
            