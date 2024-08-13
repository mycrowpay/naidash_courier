# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, route, SessionExpiredException
from odoo.service import security
from odoo.service.security import check_session

logger = logging.getLogger(__name__)

class NaidashPriority(http.Controller):
    @route('/api/v1/naidash/priority', methods=['POST'], auth='user', type='json')
    def create_priority(self, **kw):
        """Create the priority
        """ 

        try:            
            request_data = json.loads(request.httprequest.data)                        
            priority_details = request.env['courier.priority.custom'].create_priority(request_data)
            return priority_details
        except Exception as e:
            logger.exception(f"The following error occurred while creating the priority:\n\n{str(e)}")
            return {
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/priority/<int:priority_id>', methods=['PATCH'], auth='user', type='json')
    def edit_priority(self, priority_id, **kw):
        """Edit the priority details
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            priority_details = request.env['courier.priority.custom'].edit_priority(priority_id, request_data)
            return priority_details
        except TypeError as e:
            logger.error(f"This datatype error ocurred while modifying the priority:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }        
        except Exception as e:
            logger.exception(f"This error occurred while modifying the priority:\n\n{str(e)}")
            return {            
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/priority/<int:priority_id>', methods=['GET'], auth='user', type='http')
    def get_priority(self, priority_id):
        """Get the priority details
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:
            priority_details = request.env['courier.priority.custom'].get_priority(priority_id)
            status_code = priority_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": priority_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": priority_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the priority details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/naidash/priority', methods=['GET'], auth='user', type='http')
    def get_priorities(self):
        """
        Returns all priorities
        """ 
        
        headers = [
            ('Content-Type', 'application/json')
        ]
                
        try:
            priority_details = request.env['courier.priority.custom'].get_all_priorities()
            status_code = priority_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": priority_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:                
                data = json.dumps(
                    {
                        "result": priority_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the priorities:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)}
                }
            )
            
            return request.make_response(data, headers, status=500)
            