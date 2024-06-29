# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, route
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