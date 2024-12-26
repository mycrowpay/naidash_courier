# -*- coding: utf-8 -*-
from datetime import datetime
import json
import logging

from odoo import http
from odoo.http import request, route, SessionExpiredException
from odoo.service import security
from werkzeug.http import HTTP_STATUS_CODES
from werkzeug.exceptions import (NotFound, BadRequest, Unauthorized, HTTPException, Forbidden, 
                                 MethodNotAllowed, RequestTimeout, Conflict, UnprocessableEntity, 
                                 InternalServerError, GatewayTimeout, ServiceUnavailable)
from odoo.exceptions import UserError, MissingError, AccessError, AccessDenied

logger = logging.getLogger(__name__)

class NaidashSalesOrder(http.Controller):
    @route('/api/v1/naidash/sale', methods=['POST'], auth='user', type='json')
    def create_sales_order(self, **kw):
        """Create the sale order
        """ 
                        
        try:
            request_data = json.loads(request.httprequest.data)                        
            sale_order_details = request.env['sale.order'].create_sales_order(request_data)
            return sale_order_details
        except TypeError as e:
            logger.error(f"This datatype error ocurred while creating the sale order:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }      
        except Exception as e:
            logger.exception(f"This error occurred while creating the sale order:\n\n{str(e)}")
            return {                
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/sale/<int:sale_id>', methods=['GET'], auth='user', type='http')
    def get_sales_order(self, sale_id):
        """Get the sales order details
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:
            sale_order_details = request.env['sale.order'].get_a_sales_order(sale_id)
            status_code = sale_order_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": sale_order_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": sale_order_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the sale order details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/naidash/sale', methods=['GET'], auth='user', type='http')
    def get_all_sales_orders(self):
        """
        Returns all sales orders based on the query parameter(s).
        """ 
        
        headers = [
            ('Content-Type', 'application/json')
        ]
                
        try:
            query_params = dict()
            
            partner_id = request.params.get('partner_id')
            stage = request.params.get('stage')
            quotation_date_from = request.params.get('quotation_date_from')
            quotation_date_to = request.params.get('quotation_date_to')
            delivery_date_from = request.params.get('delivery_date_from')
            delivery_date_to = request.params.get('delivery_date_to')
            created_date_from = request.params.get('created_date_from')
            created_date_to = request.params.get('created_date_to')
            
            if partner_id:
                query_params["partner_id"] = int(partner_id)
            if stage:
                query_params["stage"] = stage
            if quotation_date_from and quotation_date_to:
                query_params["quotation_date_from"] = datetime.strptime(quotation_date_from, "%Y-%m-%d")
                query_params["quotation_date_to"] = datetime.strptime(quotation_date_to, "%Y-%m-%d")
            if delivery_date_from and delivery_date_to:
                query_params["delivery_date_from"] = datetime.strptime(delivery_date_from, "%Y-%m-%d")
                query_params["delivery_date_to"] = datetime.strptime(delivery_date_to, "%Y-%m-%d")
            if created_date_from and created_date_to:
                query_params["created_date_from"] = datetime.strptime(created_date_from, "%Y-%m-%d")
                query_params["created_date_to"] = datetime.strptime(created_date_to, "%Y-%m-%d")
            
            if not query_params:
                data = json.dumps(
                    {
                        "error": {
                            "code": 400,
                            "message": "Bad Request"
                        }
                    }
                )

                return request.make_response(data, headers, status=400)             
            
            sale_order_details = request.env['sale.order'].get_all_sales_orders(query_params)
            status_code = sale_order_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": sale_order_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:                
                data = json.dumps(
                    {
                        "result": sale_order_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the sales orders:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/naidash/sale/<int:sale_id>/confirm', methods=['GET'], auth='user', type='http')
    def confirm_the_sales_order(self, sale_id):
        """Confirm the sales order details
        """      
                
        headers = [('Content-Type', 'application/json')]                
        try:
            sale_order_details = request.env['sale.order'].confirm_sales_order(sale_id)
            status_code = sale_order_details.get("code")
            
            if status_code != 200:
                data = json.dumps(
                    {
                        "error": sale_order_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": sale_order_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while confirming the sale order:\n\n{str(e)}")
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
        
    @route('/api/v1/naidash/sale/<int:sale_id>/cancel', methods=['GET'], auth='user', type='http')
    def cancel_the_sales_order(self, sale_id):
        """Cancel the sales order
        """      
                
        headers = [('Content-Type', 'application/json')]                
        try:
            sale_order_details = request.env['sale.order'].cancel_sales_order(sale_id)
            status_code = sale_order_details.get("code")
            
            if status_code != 200:
                data = json.dumps(
                    {
                        "error": sale_order_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": sale_order_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while cancelling the sales order:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/naidash/sale/<int:sale_id>/draft', methods=['GET'], auth='user', type='http')
    def reset_the_sales_order(self, sale_id):
        """Reset the sales order to draft
        """      
                
        headers = [('Content-Type', 'application/json')]                
        try:
            sale_order_details = request.env['sale.order'].reset_the_sales_order_to_draft(sale_id)
            status_code = sale_order_details.get("code")
            
            if status_code != 200:
                data = json.dumps(
                    {
                        "error": sale_order_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": sale_order_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while resetting the sales order:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)