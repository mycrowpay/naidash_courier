# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, route

import json
import logging


logger = logging.getLogger(__name__)

class NaidashCourier(http.Controller):
    @route('/api/v1/naidash/stage', methods=['POST'], auth='user', type='json')
    def create_stage(self, **kw):
        """Create the stage
        """ 
                        
        try:
            request_data = json.loads(request.httprequest.data)                        
            stage_details = request.env['courier.stage.custom'].create_stage(request_data)
            return stage_details
        except Exception as e:
            logger.exception(f"The following error occurred while creating the stage:\n\n{str(e)}")
            return {                
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/stage/<int:stage_id>', methods=['PATCH'], auth='user', type='json')
    def edit_stage(self, stage_id, **kw):
        """Edit the stage details
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            stage_details = request.env['courier.stage.custom'].edit_stage_details(stage_id, request_data)
            return stage_details
        except Exception as e:
            logger.exception(f"The following error occurred while modifying the stage:\n\n{str(e)}")
            return {            
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/stage/<int:stage_id>', methods=['GET'], auth='user', type='http')
    def get_stage(self, stage_id):
        """Get the stage details
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:
            stage_details = request.env['courier.stage.custom'].get_a_stage(stage_id)
            status_code = stage_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": stage_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": stage_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the stage details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)}
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/naidash/stage', methods=['GET'], auth='user', type='http')
    def get_all_stages(self):
        """
        Returns all `active` stages by default if no value is provided in the `search` parameter.
        Possible values that can be passed in the `search` parameter are `inactive` or `all`.
        """ 
        
        query_params = []
        headers = [
            ('Content-Type', 'application/json')
        ]
                
        try:
            search_param_values = ["inactive", "all", "", None]
            search = request.params.get('search')
            
            if search not in search_param_values:
                data = json.dumps(
                    {
                        "error": {
                            "code": 400,
                            "message": "Bad Request"
                        }
                    }
                )

                return request.make_response(data, headers, status=400)                
            else:   
                if search == "inactive":
                    query_params = [('active','=', False)]
                elif search == "all":
                    query_params = [
                        '|',
                        ('active','=', True),
                        ('active','=', False)
                    ]
    
                stage_details = request.env['courier.stage.custom'].get_all_stages(query_params)
                status_code = stage_details.get("code")
                
                if status_code == 404:
                    data = json.dumps(
                        {
                            "error": stage_details
                        }
                    )

                    return request.make_response(data, headers, status=status_code)
                else:                
                    data = json.dumps(
                        {
                            "result": stage_details
                        }
                    )

                    return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the stages:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)}
                }
            )
            
            return request.make_response(data, headers, status=500)