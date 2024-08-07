# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, route, SessionExpiredException
from odoo.service import security
from odoo.service.security import check_session

logger = logging.getLogger(__name__)

class NaidashStage(http.Controller):
    @route('/api/v1/naidash/category', methods=['POST'], auth='user', type='json')
    def create_category(self, **kw):
        """Create the category
        """ 

        try:            
            request_data = json.loads(request.httprequest.data)                        
            category_details = request.env['courier.category.custom'].create_category(request_data)
            return category_details
        except Exception as e:
            logger.exception(f"The following error occurred while creating the category:\n\n{str(e)}")
            return {
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/category/<int:category_id>', methods=['PATCH'], auth='user', type='json')
    def edit_category(self, category_id, **kw):
        """Edit the category details
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            category_details = request.env['courier.category.custom'].edit_category(category_id, request_data)
            return category_details
        except TypeError as e:
            logger.error(f"This datatype error ocurred while modifying the category:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }        
        except Exception as e:
            logger.exception(f"This error occurred while modifying the category:\n\n{str(e)}")
            return {            
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/category/<int:category_id>', methods=['GET'], auth='user', type='http')
    def get_category(self, category_id):
        """Get the category details
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:
            category_details = request.env['courier.category.custom'].get_category(category_id)
            status_code = category_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": category_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": category_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the category details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/naidash/category', methods=['GET'], auth='user', type='http')
    def get_categories(self):
        """
        Returns all categories
        """ 
        
        headers = [
            ('Content-Type', 'application/json')
        ]
                
        try:
            category_details = request.env['courier.category.custom'].get_all_categories()
            status_code = category_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": category_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:                
                data = json.dumps(
                    {
                        "result": category_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the categories:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)}
                }
            )
            
            return request.make_response(data, headers, status=500)
            