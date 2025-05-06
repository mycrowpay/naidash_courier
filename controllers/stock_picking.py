# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, route, SessionExpiredException
from odoo.service import security
from odoo.service.security import check_session

logger = logging.getLogger(__name__)

class StockPicking(http.Controller):
    @route('/api/v1/stock_picking', methods=['POST'], auth='user', type='json')
    def create_stock_picking(self, **kw):
        """Create the stock picking details
        """ 

        try:            
            request_data = json.loads(request.httprequest.data)                        
            stock_picking_details = request.env['stock.picking'].create_the_stock_picking(request_data)
            return stock_picking_details
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            return {
                "code": 401,
                "message": "Session expired. Please log in again."
            }
        except Exception as e:
            logger.exception(f"The following error occurred while creating the stock picking details:\n\n{str(e)}")
            return {
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/stock_picking/<int:stock_picking_id>', methods=['PATCH'], auth='user', type='json')
    def edit_stock_picking(self, stock_picking_id, **kw):
        """Edit the stock picking details
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            stock_picking_details = request.env['stock.picking'].edit_the_stock_picking(stock_picking_id, request_data)
            return stock_picking_details
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            return {
                "code": 401,
                "message": "Session expired. Please log in again."
            }
        except TypeError as e:
            logger.error(f"This datatype error ocurred while modifying the stock picking details:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }        
        except Exception as e:
            logger.exception(f"This error occurred while modifying the stock picking details:\n\n{str(e)}")
            return {            
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/stock_picking/<int:stock_picking_id>', methods=['GET'], auth='user', type='http')
    def get_stock_picking(self, stock_picking_id):
        """Get the stock picking details
        """ 
                
        headers = [('Content-Type', 'application/json')]
        
        try:
            stock_picking_details = request.env['stock.picking'].get_the_stock_picking(stock_picking_id)
            status_code = stock_picking_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": stock_picking_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": stock_picking_details
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
            logger.exception(f"The following error occurred while fetching the stock picking details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/stock_picking', methods=['GET'], auth='user', type='http')
    def get_stock_pickings(self):
        """
        Returns all the stock pickings
        """ 
        
        headers = [
            ('Content-Type', 'application/json')
        ]
                
        try:
            query_params = dict()
            the_stock_picking_type_code = request.params.get('stock_picking_type_code')
            the_scheduled_date = request.params.get('scheduled_date')
            the_status = request.params.get('status')
            
            if the_stock_picking_type_code:
                query_params["stock_picking_type_code"] = the_stock_picking_type_code
                
            if the_scheduled_date:
                query_params["scheduled_date"] = the_scheduled_date
                
            if the_status:
                query_params["status"] = the_status
            
            stock_picking_details = request.env['stock.picking'].get_all_the_stock_pickings(query_params)
            status_code = stock_picking_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": stock_picking_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:                
                data = json.dumps(
                    {
                        "result": stock_picking_details
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
            logger.exception(f"The following error occurred while fetching the stock pickings:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/stock_picking/<int:stock_picking_id>/confirm', methods=['GET'], auth='user', type='http')
    def confirm_the_stock_picking(self, stock_picking_id):
        """Confirm the stock picking details
        """      
                
        headers = [('Content-Type', 'application/json')]                
        try:
            stock_picking_details = request.env['stock.picking'].confirm_the_stock_picking_details(stock_picking_id)
            status_code = stock_picking_details.get("code")
            
            if status_code != 200:
                data = json.dumps(
                    {
                        "error": stock_picking_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": stock_picking_details
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
            logger.exception(f"The following error occurred while confirming the stock picking:\n\n{str(e)}")
            if "HTTPSConnectionPool" in str(e):
                data = json.dumps(
                    {
                        "error": {
                            "code": 504,
                            "message": "Check your internet connection"
                        }
                    }
                )
            else:
                data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
                   
            return request.make_response(data, headers, status=500)
                
    @route('/api/v1/stock_picking/<int:stock_picking_id>/validate', methods=['GET'], auth='user', type='http')
    def validate_the_stock_picking(self, stock_picking_id):
        """Validate the stock picking details
        """      
                
        headers = [('Content-Type', 'application/json')]                
        try:
            stock_picking_details = request.env['stock.picking'].validate_the_stock_picking_details(stock_picking_id)
            status_code = stock_picking_details.get("code")
            
            if status_code != 200:
                data = json.dumps(
                    {
                        "error": stock_picking_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": stock_picking_details
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
            logger.exception(f"The following error occurred while validating the stock picking:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/stock_picking/<int:stock_picking_id>/cancel', methods=['GET'], auth='user', type='http')
    def cancel_the_stock_picking(self, stock_picking_id):
        """Cancel the stock picking details
        """      
                
        headers = [('Content-Type', 'application/json')]                
        try:
            stock_picking_details = request.env['stock.picking'].cancel_the_stock_picking_details(stock_picking_id)
            status_code = stock_picking_details.get("code")
            
            if status_code != 200:
                data = json.dumps(
                    {
                        "error": stock_picking_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": stock_picking_details
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
            logger.exception(f"The following error occurred while cancelling the stock picking:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)