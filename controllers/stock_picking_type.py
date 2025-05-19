# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, route, SessionExpiredException
from odoo.service import security
from odoo.service.security import check_session

logger = logging.getLogger(__name__)

class NaidashStockPickingType(http.Controller):
    @route('/api/v1/stock_picking_type', methods=['POST'], auth='user', type='json')
    def create_stock_picking_type(self, **kw):
        """Create the stock picking type details
        """ 

        try:            
            request_data = json.loads(request.httprequest.data)                        
            stock_picking_type_details = request.env['stock.picking.type'].create_the_stock_picking_type(request_data)
            return stock_picking_type_details
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            return {
                "code": 401,
                "message": "Session expired. Please log in again."
            }
        except Exception as e:
            logger.exception(f"The following error occurred while creating the stock picking type details:\n\n{str(e)}")
            return {
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/stock_picking_type/<int:stock_picking_type_id>', methods=['PATCH'], auth='user', type='json')
    def edit_stock_picking_type(self, stock_picking_type_id, **kw):
        """Edit the stock picking type details
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            stock_picking_type_details = request.env['stock.picking.type'].edit_the_stock_picking_type(stock_picking_type_id, request_data)
            return stock_picking_type_details
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            return {
                "code": 401,
                "message": "Session expired. Please log in again."
            }
        except TypeError as e:
            logger.error(f"This datatype error ocurred while modifying the stock picking type details:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }        
        except Exception as e:
            logger.exception(f"This error occurred while modifying the stock picking type details:\n\n{str(e)}")
            return {            
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/stock_picking_type/<int:stock_picking_type_id>', methods=['GET'], auth='user', type='http')
    def get_stock_picking_type(self, stock_picking_type_id):
        """Get the stock picking type details
        """ 
                
        headers = [('Content-Type', 'application/json')]
        
        try:
            stock_picking_type_details = request.env['stock.picking.type'].get_the_stock_picking_type(stock_picking_type_id)
            status_code = stock_picking_type_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": stock_picking_type_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": stock_picking_type_details
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
            logger.exception(f"The following error occurred while fetching the stock picking type details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/stock_picking_type', methods=['GET'], auth='user', type='http')
    def get_stock_picking_types(self):
        """
        Returns all the stock picking types
        """ 
        
        headers = [
            ('Content-Type', 'application/json')
        ]
                
        try:
            query_params = dict()
            the_operation_type = request.params.get('operation_type')
            the_warehouse_id = request.params.get('warehouse_id')
            is_active = request.params.get('active')
            
            if the_operation_type:
                query_params["operation_type"] = the_operation_type
                
            if the_warehouse_id:
                query_params["warehouse_id"] = the_warehouse_id
                
            if is_active:
                query_params["active"] = is_active
                            
            stock_picking_type_details = request.env['stock.picking.type'].get_all_the_stock_picking_types(query_params)
            status_code = stock_picking_type_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": stock_picking_type_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:                
                data = json.dumps(
                    {
                        "result": stock_picking_type_details
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
            logger.exception(f"The following error occurred while fetching the stock picking types:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)