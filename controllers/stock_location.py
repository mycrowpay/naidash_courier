# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, route, SessionExpiredException
from odoo.service import security
from odoo.service.security import check_session

logger = logging.getLogger(__name__)

class NaidashStockLocation(http.Controller):
    @route('/api/v1/stock_location', methods=['POST'], auth='user', type='json')
    def create_stock_location(self, **kw):
        """Create the stock location details
        """ 

        try:            
            request_data = json.loads(request.httprequest.data)                        
            stock_location_details = request.env['stock.location'].create_the_stock_location(request_data)
            return stock_location_details
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            return {
                "code": 401,
                "message": "Session expired. Please log in again."
            }
        except Exception as e:
            logger.exception(f"The following error occurred while creating the stock location details:\n\n{str(e)}")
            return {
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/stock_location/<int:stock_location_id>', methods=['PATCH'], auth='user', type='json')
    def edit_stock_location(self, stock_location_id, **kw):
        """Edit the stock location details
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            stock_location_details = request.env['stock.location'].edit_the_stock_location(stock_location_id, request_data)
            return stock_location_details
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            return {
                "code": 401,
                "message": "Session expired. Please log in again."
            }
        except TypeError as e:
            logger.error(f"This datatype error ocurred while modifying the stock location details:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }        
        except Exception as e:
            logger.exception(f"This error occurred while modifying the stock location details:\n\n{str(e)}")
            return {            
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/stock_location/<int:stock_location_id>', methods=['GET'], auth='user', type='http')
    def get_stock_location(self, stock_location_id):
        """Get the stock location details
        """ 
                
        headers = [('Content-Type', 'application/json')]
        
        try:
            stock_location_details = request.env['stock.location'].get_the_stock_location(stock_location_id)
            status_code = stock_location_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": stock_location_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": stock_location_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 401,
                        "message": "Session expired. Please log in again."
                    }
                }
            )
            
            return request.make_response(data, headers, status=401)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the stock location details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/stock_location', methods=['GET'], auth='user', type='http')
    def get_stock_locations(self):
        """
        Returns all the stock locations
        """ 
        
        headers = [
            ('Content-Type', 'application/json')
        ]
                
        try:
            query_params = dict()
            the_location_type = request.params.get('location_type')
            the_warehouse_id = request.params.get('warehouse_id')
            is_active = request.params.get('active')
            the_parent_stock_location_id = request.params.get('parent_stock_location_id')
            
            if the_location_type:
                query_params["location_type"] = the_location_type
                
            if the_warehouse_id:
                query_params["warehouse_id"] = the_warehouse_id
                
            if the_parent_stock_location_id:
                query_params["parent_stock_location_id"] = the_parent_stock_location_id
                
            if is_active:
                query_params["active"] = is_active                
                            
            stock_location_details = request.env['stock.location'].get_all_the_stock_locations(query_params)
            status_code = stock_location_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": stock_location_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:                
                data = json.dumps(
                    {
                        "result": stock_location_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 401,
                        "message": "Session expired. Please log in again."
                    }
                }
            )
            
            return request.make_response(data, headers, status=401)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the stock locations:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)