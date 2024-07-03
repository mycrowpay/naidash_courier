# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, route, SessionExpiredException
from datetime import datetime
import json
import logging


logger = logging.getLogger(__name__)

class NaidashSaleOrder(http.Controller):
    @route('/api/v1/naidash/sale', methods=['POST'], auth='user', type='json')
    def create_sale_order(self, **kw):
        """Create the sale order
        """ 
                        
        try:
            request_data = json.loads(request.httprequest.data)                        
            sale_order_details = request.env['sale.order'].create_sale_order(request_data)
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
    def get_sale_order(self, sale_id):
        """Get the sale order details
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:
            sale_order_details = request.env['sale.order'].get_a_sale_order(sale_id)
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
                        "message": str(e)}
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/naidash/sale', methods=['GET'], auth='user', type='http')
    def get_sales_orders(self):
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
            
            sale_order_details = request.env['sale.order'].get_all_sales_orders_based_on_query_params(query_params)
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
                        "message": str(e)}
                }
            )
            
            return request.make_response(data, headers, status=500)