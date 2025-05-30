# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, route
from datetime import datetime
import json
import logging
from ..models.utils import NaidashUtils

logger = logging.getLogger(__name__)
nautils = NaidashUtils()

class NaidashCourier(http.Controller):
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
        
    @route('/api/v1/courier/<int:courier_id>/next', methods=['GET'], auth='user', type='http')
    def move_courier_to_next_stage(self, courier_id):
        """Moves a courier request to the next stage
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:
            partner_ids = list()
            courier_details = request.env['courier.custom'].move_to_next_stage(courier_id)
            status_code = courier_details.get("code")

            courier = request.env['courier.custom'].search(
                [
                    ('id', '=', int(courier_id))
                ]
            )
                            
            try:
                if courier.stage_id.person_to_notify == "sender":
                    partner_ids = [courier.sender_name_id.id]
                elif courier.stage_id.person_to_notify == "receiver":
                    partner_ids = [courier.receiver_name_id.id]
                elif courier.stage_id.person_to_notify == "both":
                    partner_ids = [courier.sender_name_id.id, courier.receiver_name_id.id]
                                    
                if courier.stage_id.notification_type == "sms":
                    courier_template_id = courier.stage_id.template_id
                    if courier_template_id and partner_ids:
                        nautils.send_sms_using_template(courier_template_id.id, courier.id, partner_ids)
                    else:
                        data = json.dumps(
                            {
                                "error": {
                                    "code": 404,
                                    "message": "Template or partner not found"
                                }
                            }
                        )
                        
                        return request.make_response(data, headers, status=500)
                elif courier.stage_id.notification_type == "email":
                    # Send email to the partner
                    pass
            except Exception as e:
                logger.exception(f"Exception error ocurred while sending the SMS:\n\n{str(e)}")
                if "HTTPSConnectionPool" in str(e):
                    data = json.dumps(
                        {
                            "error": {
                                "code": 500,
                                "message": "Check your internet connection"
                            }
                        }
                    )                    
                else:
                    data = json.dumps(
                    {
                        "error": {
                            "code": 500,
                            "message": str(e)
                        }
                    }
                )
                
                return request.make_response(data, headers, status=500)
            
            if status_code == 403 or status_code == 404:
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
            logger.exception(f"The following error occurred while moving the courier request to the next stage:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/courier/<int:courier_id>/previous', methods=['GET'], auth='user', type='http')
    def move_courier_to_previous_stage(self, courier_id):
        """Moves a courier request to the previous stage
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:
            courier_details = request.env['courier.custom'].move_to_previous_stage(courier_id)
            status_code = courier_details.get("code")
            
            if status_code == 403 or status_code == 404:
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
            logger.exception(f"The following error occurred while moving the courier request to the previous stage:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/courier/<int:courier_id>/cancel', methods=['GET'], auth='user', type='http')
    def move_courier_to_cancel_stage(self, courier_id):
        """Moves a courier request to the cancellation stage
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:
            courier_details = request.env['courier.custom'].move_to_cancel_stage(courier_id)
            status_code = courier_details.get("code")
            
            if status_code == 403 or status_code == 404:
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
            logger.exception(f"The following error occurred while moving the courier request to the cancellation stage:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)