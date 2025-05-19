# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, route, SessionExpiredException
from odoo.service import security
from odoo.service.security import check_session

logger = logging.getLogger(__name__)

class NaidashStockWarehouse(http.Controller):
    @route('/api/v1/warehouse', methods=['POST'], auth='user', type='json')
    def create_warehouse(self, **kw):
        """Create the warehouse details
        """ 

        try:            
            request_data = json.loads(request.httprequest.data)                        
            warehouse_details = request.env['stock.warehouse'].create_the_warehouse(request_data)
            return warehouse_details
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            return {
                "code": 401,
                "message": "Session expired. Please log in again."
            }
        except Exception as e:
            logger.exception(f"The following error occurred while creating the warehouse details:\n\n{str(e)}")
            return {
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/warehouse/<int:warehouse_id>', methods=['PATCH'], auth='user', type='json')
    def edit_warehouse(self, warehouse_id, **kw):
        """Edit the warehouse details
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            warehouse_details = request.env['stock.warehouse'].edit_the_warehouse(warehouse_id, request_data)
            return warehouse_details
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            return {
                "code": 401,
                "message": "Session expired. Please log in again."
            }
        except TypeError as e:
            logger.error(f"This datatype error ocurred while modifying the warehouse details:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }        
        except Exception as e:
            logger.exception(f"This error occurred while modifying the warehouse details:\n\n{str(e)}")
            return {            
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/warehouse/<int:warehouse_id>', methods=['GET'], auth='user', type='http')
    def get_warehouse(self, warehouse_id):
        """Get the warehouse details
        """ 
                
        headers = [('Content-Type', 'application/json')]
        
        try:
            warehouse_details = request.env['stock.warehouse'].get_the_warehouse(warehouse_id)
            status_code = warehouse_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": warehouse_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": warehouse_details
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
            logger.exception(f"The following error occurred while fetching the warehouse details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/warehouse', methods=['GET'], auth='user', type='http')
    def get_warehouses(self):
        """
        Returns all the warehouses
        """ 
        
        headers = [
            ('Content-Type', 'application/json')
        ]
                
        try:
            query_params = dict()
            is_active = request.params.get('active')
                
            if is_active:
                query_params["active"] = is_active
                            
            warehouse_details = request.env['stock.warehouse'].get_all_the_warehouses(query_params)
            status_code = warehouse_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": warehouse_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:                
                data = json.dumps(
                    {
                        "result": warehouse_details
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
            logger.exception(f"The following error occurred while fetching the warehouses:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)