# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

import json
import logging


logger = logging.getLogger(__name__)

class NaidashCourier(http.Controller):
    @http.route('/api/v1/naidash/stage', methods=['POST'], auth='user', type='json')
    def create_stage(self, **kw):
        """Create the stage
        """ 
                        
        try:
            request_data = json.loads(request.httprequest.data)                        
            stage_details = request.env['courier.stage.custom'].create_stage(request_data)
            return stage_details
        except Exception as e:
            logger.exception(f"Error: The following error occurred while creating the stage:\n\n{str(e)}")
            return {                
                "status_code": 500,
                "error": str(e)
            }
            
    @http.route('/api/v1/naidash/stage/<int:stage_id>', methods=['PATCH'], auth='user', type='json')
    def edit_stage(self, stage_id, **kw):
        """Edit the stage details
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            stage_details = request.env['courier.stage.custom'].edit_stage_details(stage_id, request_data)
            return stage_details
        except Exception as e:
            logger.exception(f"Error: The following error occurred while modifying the stage:\n\n{str(e)}")
            return {            
                "status_code": 500,
                "error": str(e)
            }
            
    @http.route('/api/v1/naidash/stage/<int:stage_id>', methods=['GET'], auth='user', type='http')
    def get_stage(self, stage_id):
        """Get the stage details
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:
            stage_details = request.env['courier.stage.custom'].get_stage_details(stage_id)
            status_code = stage_details.get("status_code")
            data = json.dumps(
                {
                    "result": stage_details
                }
            )

            return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"Error: The following error occurred while fetching the stage details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "status_code": 500,
                        "message": str(e)}
                }
            )
            
            return request.make_response(data, headers, status=500)