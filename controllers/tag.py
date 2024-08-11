# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, route, SessionExpiredException
from odoo.service import security
from odoo.service.security import check_session

logger = logging.getLogger(__name__)

class NaidashTag(http.Controller):
    @route('/api/v1/naidash/tag', methods=['POST'], auth='user', type='json')
    def create_tag(self, **kw):
        """Create the tag
        """ 

        try:            
            request_data = json.loads(request.httprequest.data)                        
            tag_details = request.env['courier.tag.custom'].create_tag(request_data)
            return tag_details
        except Exception as e:
            logger.exception(f"The following error occurred while creating the tag:\n\n{str(e)}")
            return {
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/tag/<int:tag_id>', methods=['PATCH'], auth='user', type='json')
    def edit_tag(self, tag_id, **kw):
        """Edit the tag details
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            tag_details = request.env['courier.tag.custom'].edit_tag(tag_id, request_data)
            return tag_details
        except TypeError as e:
            logger.error(f"This datatype error ocurred while modifying the tag:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }        
        except Exception as e:
            logger.exception(f"This error occurred while modifying the tag:\n\n{str(e)}")
            return {            
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/tag/<int:tag_id>', methods=['GET'], auth='user', type='http')
    def get_tag(self, tag_id):
        """Get the tag details
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:
            tag_details = request.env['courier.tag.custom'].get_tag(tag_id)
            status_code = tag_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": tag_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": tag_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the tag details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/naidash/tag', methods=['GET'], auth='user', type='http')
    def get_tags(self):
        """
        Returns all tags
        """ 
        
        headers = [
            ('Content-Type', 'application/json')
        ]
                
        try:
            tag_details = request.env['courier.tag.custom'].get_all_tags()
            status_code = tag_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": tag_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:                
                data = json.dumps(
                    {
                        "result": tag_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the tags:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)}
                }
            )
            
            return request.make_response(data, headers, status=500)
            