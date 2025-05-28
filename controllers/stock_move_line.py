# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, route, SessionExpiredException
from odoo.service import security
from odoo.service.security import check_session

logger = logging.getLogger(__name__)

class NaidashStockMoveLine(http.Controller):
    @route('/api/v1/stock_move_line', methods=['POST'], auth='user', type='json')
    def create_stock_move_line(self, **kw):
        """Create the stock move line details
        """ 

        try:            
            request_data = json.loads(request.httprequest.data)                        
            stock_move_line_details = request.env['stock.move.line'].create_the_stock_move_line(request_data)
            return stock_move_line_details
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            return {
                "code": 401,
                "message": "Session expired. Please log in again."
            }
        except Exception as e:
            logger.exception(f"The following error occurred while creating the stock move line details:\n\n{str(e)}")
            return {
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/stock_move_line/<int:stock_move_line_id>', methods=['PATCH'], auth='user', type='json')
    def edit_stock_move_line(self, stock_move_line_id, **kw):
        """Edit the stock move line details
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            stock_move_line_details = request.env['stock.move.line'].edit_the_stock_move_line(stock_move_line_id, request_data)
            return stock_move_line_details
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            return {
                "code": 401,
                "message": "Session expired. Please log in again."
            }
        except TypeError as e:
            logger.error(f"This datatype error ocurred while modifying the stock move line details:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }        
        except Exception as e:
            logger.exception(f"This error occurred while modifying the stock move line details:\n\n{str(e)}")
            return {            
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/stock_move_line/<int:stock_move_line_id>', methods=['GET'], auth='user', type='http')
    def get_stock_move_line(self, stock_move_line_id):
        """Get the stock move line details
        """ 
                
        headers = [('Content-Type', 'application/json')]
        
        try:
            stock_move_line_details = request.env['stock.move.line'].get_the_stock_move_line(stock_move_line_id)
            status_code = stock_move_line_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": stock_move_line_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": stock_move_line_details
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
            logger.exception(f"The following error occurred while fetching the stock move line details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/stock_move_line', methods=['GET'], auth='user', type='http')
    def get_stock_move_lines(self):
        """
        Returns all the stock move lines
        """ 
        
        headers = [
            ('Content-Type', 'application/json')
        ]
                
        try:
            query_params = dict()
            the_stock_picking_id = request.params.get('stock_picking_id')
            the_stock_move_id = request.params.get('stock_move_id')
            
            if the_stock_picking_id:
                query_params["stock_picking_id"] = int(the_stock_picking_id)
                
            if the_stock_move_id:
                query_params["stock_move_id"] = int(the_stock_move_id)
                
            if not query_params:
                data = json.dumps(
                    {
                        "error": {
                            "code": 400,
                            "message": "Bad Request! Stock picking ID or stock move ID is required."
                        }
                    }
                )

                return request.make_response(data, headers, status=400)
            
            stock_move_line_details = request.env['stock.move.line'].get_all_the_stock_move_lines(query_params)
            status_code = stock_move_line_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": stock_move_line_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:                
                data = json.dumps(
                    {
                        "result": stock_move_line_details
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
            logger.exception(f"The following error occurred while fetching the stock move lines:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)