import logging
import requests

from datetime import datetime
from odoo import models, _, fields, api
from odoo.http import request, SessionExpiredException
from odoo.exceptions import ValidationError, UserError

logger = logging.getLogger(__name__)

class NaidashPriority(models.Model):
    _inherit = "courier.priority.custom"
    _order = "name asc"
    
    def create_priority(self, request_data):
        """Create the priority
        """ 
        
        try:
            data = dict()
            response_data = dict()
            param_values = ["", None]
            
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:            
                priority_name = request_data.get("name")
                product_id = request_data.get("product_id")
                charges = request_data.get("charges")
                
                if priority_name in param_values:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `name` parameter"
                    return response_data
                
                if not product_id:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `product_id` parameter"
                    return response_data
                
                priority_name = (request_data.get("name")).strip()
                
                vals = {
                    "name": priority_name,
                    "charges": charges,
                    "product_id": int(product_id)
                }
                                
                priority = self.env['courier.priority.custom'].create(vals)

                if priority:
                    data['id'] = priority.id
                    response_data["code"] = 201                
                    response_data["message"] = "Created successfully"
                    response_data["data"] = data
            else:
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"An error ocurred while creating the priority:\n\n{str(e)}")
            raise e
        
    def edit_priority(self, priority_id, request_data):
        """Edit the priority details
        """ 
                
        try:
            response_data = dict()
            search_param_values = ["", None]
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:
                priority = self.env['courier.priority.custom'].search(
                    [
                        ('id','=', int(priority_id)), '|', 
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if priority:
                    priority_details = dict()
                                
                    if request_data.get("name") not in search_param_values:
                        priority_details["name"] = (request_data.get("name")).strip()
                        
                    if request_data.get("charges") not in search_param_values:
                        priority_details["charges"] = request_data.get("charges")
                        
                    if request_data.get("product_id") not in search_param_values:
                        priority_details["product_id"] = int(request_data.get("product_id"))

                    if request_data.get("active") not in search_param_values:
                        priority_details["active"] = request_data.get("active")
                        
                    # Update priority details
                    if priority_details:
                        priority.write(priority_details)
                        response_data["code"] = 200
                        response_data["message"] = "Updated successfully"
                    else:
                        response_data["code"] = 204
                        response_data["message"] = "Nothing to update"
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Priority Not Found!"                    
            else:
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data        
        except TypeError as e:
            logger.error(f"Datatype error ocurred while modifying the priority:\n\n{str(e)}")
            raise e        
        except Exception as e:
            logger.error(f"An error ocurred while modifying the priority:\n\n{str(e)}")
            raise e
        
    def get_priority(self, priority_id):
        """Get the priority details
        """        
        
        try:
            data = dict()            
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for 
            # any priority regardless of the active status
            if is_courier_manager:
                priority = self.env['courier.priority.custom'].search(
                    [
                        ('id','=', int(priority_id)), '|', 
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if priority:
                    data["id"] = priority.id
                    data["name"] = priority.name
                    data["charges"] = priority.charges
                    data["active"] = priority.active
                    data["product"] = {"id": priority.product_id.id, "name": priority.product_id.name} if priority.product_id else {}
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = data
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Priority Not Found!"
            else: 
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the priority details:\n\n{str(e)}")
            raise e
        
    def get_all_priorities(self):
        """Get all the priorities
        """        
        
        try:
            response_data = dict()
            all_priorities = []
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for 
            # any priority regardless of the active status
            if is_courier_manager:
                priorities = self.env['courier.priority.custom'].search(
                    [
                        '|',
                        ('active','=', True),
                        ('active','=', False)
                    ], order='name asc')
                
                if priorities:
                    for priority in priorities:
                        data = dict()                    
                        data["id"] = priority.id
                        data["name"] = priority.name
                        data["charges"] = priority.charges
                        data["active"] = priority.active
                        data["product"] = {"id": priority.product_id.id, "name": priority.product_id.name} if priority.product_id else {}
                        
                        all_priorities.append(data)
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = all_priorities
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Priority Not Found!"
            else: 
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the priorities:\n\n{str(e)}")
            raise e