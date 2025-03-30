# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, route, SessionExpiredException
from odoo.service import security
from odoo.service.security import check_session

logger = logging.getLogger(__name__)

class NaidashProduct(http.Controller):
    @route('/api/v1/naidash/product', methods=['POST'], auth='user', type='json')
    def create_product(self, **kw):
        """Create the product details
        """ 

        try:            
            request_data = json.loads(request.httprequest.data)                        
            product_details = request.env['product.product'].create_the_product(request_data)
            return product_details
        except Exception as e:
            logger.exception(f"The following error occurred while creating the product details:\n\n{str(e)}")
            return {
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/product/<int:product_id>', methods=['PATCH'], auth='user', type='json')
    def edit_product(self, product_id, **kw):
        """Edit the product details
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            product_details = request.env['product.product'].edit_the_product(product_id, request_data)
            return product_details
        except TypeError as e:
            logger.error(f"This datatype error ocurred while modifying the product details:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }        
        except Exception as e:
            logger.exception(f"This error occurred while modifying the product details:\n\n{str(e)}")
            return {            
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/product/<int:product_id>', methods=['GET'], auth='user', type='http')
    def get_product(self, product_id):
        """Get the product details
        """ 
                
        headers = [('Content-Type', 'application/json')]
        
        try:
            product_details = request.env['product.product'].get_the_product(product_id)
            status_code = product_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": product_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": product_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the product details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/naidash/product', methods=['GET'], auth='user', type='http')
    def get_products(self):
        """
        Returns all the products
        """ 
        
        headers = [
            ('Content-Type', 'application/json')
        ]
                
        try:
            query_params = dict()
            is_active = request.params.get('active')
            product_type = request.params.get('type')
            
            if is_active:
                query_params["active"] = is_active
                
            if product_type:
                query_params["type"] = product_type                
            
            product_details = request.env['product.product'].get_all_the_products(query_params)
            status_code = product_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": product_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:                
                data = json.dumps(
                    {
                        "result": product_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the products:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)}
                }
            )
            
            return request.make_response(data, headers, status=500)
            