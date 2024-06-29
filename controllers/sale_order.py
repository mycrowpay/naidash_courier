# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, route
from datetime import datetime
import json
import logging


logger = logging.getLogger(__name__)

class NaidashSaleOrder(http.Controller):
    @route('/api/v1/naidash/sale', methods=['POST'], auth='user', type='json')
    def create_courier(self, **kw):
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