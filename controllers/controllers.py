# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, route
from datetime import datetime
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
        except TypeError as e:
            logger.error(f"This datatype error ocurred while modifying the stage:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }        
        except Exception as e:
            logger.exception(f"This error occurred while modifying the stage:\n\n{str(e)}")
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
        
    @route('/api/v1/naidash/courier', methods=['POST'], auth='user', type='json')
    def create_courier(self, **kw):
        """Create the courier request
        """ 
                        
        try:
            request_data = json.loads(request.httprequest.data)                        
            courier_details = request.env['courier.custom'].create_courier_request(request_data)
            return courier_details
        except TypeError as e:
            logger.error(f"This datatype error ocurred while creating the courier request:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }      
        except Exception as e:
            logger.exception(f"This error occurred while creating the courier request:\n\n{str(e)}")
            return {                
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/courier/<int:courier_id>', methods=['PATCH'], auth='user', type='json')
    def edit_courier(self, courier_id, **kw):
        """Edit the courier details
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            courier_details = request.env['courier.custom'].edit_courier_request(courier_id, request_data)
            return courier_details
        except TypeError as e:
            logger.error(f"This datatype error ocurred while modifying the courier request:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }        
        except Exception as e:
            logger.exception(f"This error occurred while modifying the courier request:\n\n{str(e)}")
            return {            
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/naidash/courier/<int:courier_id>', methods=['GET'], auth='user', type='http')
    def get_courier(self, courier_id):
        """Get the courier details
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:
            courier_details = request.env['courier.custom'].get_a_courier_request(courier_id)
            status_code = courier_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": courier_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": courier_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the courier details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)}
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/naidash/courier', methods=['GET'], auth='user', type='http')
    def get_couriers(self):
        """
        Returns all courier requests based on a search parameter.
        """ 
        
        headers = [
            ('Content-Type', 'application/json')
        ]
                
        try:
            request_data = dict()
            
            phone = request.params.get('phone')
            delivery_date = request.params.get('delivery_date')
            assigned_user_id = request.params.get('assigned_user_id')
            stage_id = request.params.get('stage_id')
            priority_id = request.params.get('priority_id')
            category_id = request.params.get('category_id')
            courier_type = request.params.get('courier_type')
            is_drop_shipping = request.params.get('is_drop_shipping')
            is_record_active = request.params.get('is_record_active')
            
            if phone:
                request_data["phone"] = phone
            if delivery_date:
                request_data["delivery_date"] = datetime.strptime(delivery_date, "%Y-%m-%d")
            if assigned_user_id:
                request_data["assigned_user_id"] = int(assigned_user_id)
            if stage_id:
                request_data["stage_id"] = int(stage_id)
            if priority_id:
                request_data["priority_id"] = int(priority_id)
            if category_id:
                request_data["category_id"] = int(category_id)
            if courier_type:
                request_data["courier_type"] = courier_type
            if is_drop_shipping == "true" or is_drop_shipping == "false":
                request_data["is_drop_shipping"] = True if is_drop_shipping == "true" else False
            if is_record_active == "true" or is_record_active == "false":
                request_data["is_record_active"] = True if is_record_active == "true" else False
            
            if not request_data:
                data = json.dumps(
                    {
                        "error": {
                            "code": 400,
                            "message": "Bad Request"
                        }
                    }
                )

                return request.make_response(data, headers, status=400)             
            
            courier_details = request.env['courier.custom'].get_all_courier_requests(request_data)
            status_code = courier_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": courier_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:                
                data = json.dumps(
                    {
                        "result": courier_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the courier details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)}
                }
            )
            
            return request.make_response(data, headers, status=500)