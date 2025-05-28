# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, route, SessionExpiredException
from odoo.service import security
from odoo.service.security import check_session

logger = logging.getLogger(__name__)

class NaidashStockMove(http.Controller):
    @route('/api/v1/stock_move', methods=['POST'], auth='user', type='json')
    def create_stock_move(self, **kw):
        """Create the stock move details
        """ 

        try:            
            request_data = json.loads(request.httprequest.data)                        
            stock_move_details = request.env['stock.move'].create_the_stock_move(request_data)
            return stock_move_details
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            return {
                "code": 401,
                "message": "Session expired. Please log in again."
            }
        except Exception as e:
            logger.exception(f"The following error occurred while creating the stock move details:\n\n{str(e)}")
            return {
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/stock_move/<int:stock_move_id>', methods=['PATCH'], auth='user', type='json')
    def edit_stock_move(self, stock_move_id, **kw):
        """Edit the stock move details
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            stock_move_details = request.env['stock.move'].edit_the_stock_move(stock_move_id, request_data)
            return stock_move_details
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            return {
                "code": 401,
                "message": "Session expired. Please log in again."
            }
        except TypeError as e:
            logger.error(f"This datatype error ocurred while modifying the stock move details:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }        
        except Exception as e:
            logger.exception(f"This error occurred while modifying the stock move details:\n\n{str(e)}")
            return {            
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/stock_move/<int:stock_move_id>', methods=['GET'], auth='user', type='http')
    def get_stock_move(self, stock_move_id):
        """Get the stock move details
        """ 
                
        headers = [('Content-Type', 'application/json')]
        
        try:
            stock_move_details = request.env['stock.move'].get_the_stock_move(stock_move_id)
            status_code = stock_move_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": stock_move_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": stock_move_details
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
            logger.exception(f"The following error occurred while fetching the stock move details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/stock_move', methods=['GET'], auth='user', type='http')
    def get_stock_moves(self):
        """
        Returns all the stock moves
        """ 
        
        headers = [
            ('Content-Type', 'application/json')
        ]
                
        try:
            query_params = dict()
            the_stock_picking_id = request.params.get('stock_picking_id')
            
            if the_stock_picking_id:
                query_params["stock_picking_id"] = the_stock_picking_id
                            
            stock_move_details = request.env['stock.move'].get_all_the_stock_moves(query_params)
            status_code = stock_move_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": stock_move_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:                
                data = json.dumps(
                    {
                        "result": stock_move_details
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
            logger.exception(f"The following error occurred while fetching the stock moves:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/stock_move/<int:stock_move_id>/serial_numbers', methods=['PATCH'], auth='user', type='json')
    def assign_serial_numbers_to_stock_move(self, stock_move_id, **kw):
        """Assign serial numbers to a stock move item
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            stock_move_details = request.env['stock.move'].assign_serial_numbers_to_stock_move(stock_move_id, request_data)
            return stock_move_details
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            return {
                "code": 401,
                "message": "Session expired. Please log in again."
            }
        except TypeError as e:
            logger.error(f"This datatype error ocurred while assigning serial numbers to the stock move item:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }        
        except Exception as e:
            logger.exception(f"This error occurred while assigning serial numbers to the stock move item:\n\n{str(e)}")
            return {            
                "code": 500,
                "message": str(e)
            }