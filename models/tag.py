import logging
import requests

from datetime import datetime
from odoo import models, _, fields, api
from odoo.http import request, SessionExpiredException
from odoo.exceptions import ValidationError, UserError

logger = logging.getLogger(__name__)

class NaidashTag(models.Model):
    _inherit = "courier.tag.custom"
    _order = "name asc"
    
    def create_tag(self, request_data):
        """Create the tag
        """ 
        
        try:
            data = dict()
            response_data = dict()
            param_values = ["", None]            
            
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:            
                tag_name = request_data.get("name")
                
                if tag_name in param_values:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `name` parameter"
                    return response_data
                
                tag_name = (request_data.get("name")).strip()                
                tag = self.env['courier.tag.custom'].create({"name": tag_name})

                if tag:
                    data['id'] = tag.id
                    response_data["code"] = 201                
                    response_data["message"] = "Created successfully"
                    response_data["data"] = data
            else:
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"An error ocurred while creating the tag:\n\n{str(e)}")
            raise e
        
    def edit_tag(self, tag_id, request_data):
        """Edit the tag details
        """ 
                
        try:
            response_data = dict()
            search_param_values = ["", None]
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:
                tag = self.env['courier.tag.custom'].search(
                    [
                        ('id','=', int(tag_id)), '|', 
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if tag:
                    tag_details = dict()
                                
                    if request_data.get("name") not in search_param_values:
                        tag_details["name"] = (request_data.get("name")).strip()

                    if request_data.get("active") not in search_param_values:
                        tag_details["active"] = request_data.get("active")
                        
                    # Update tag details
                    if tag_details:
                        tag.write(tag_details)
                        response_data["code"] = 200
                        response_data["message"] = "Updated successfully"
                    else:
                        response_data["code"] = 204
                        response_data["message"] = "Nothing to update"
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Tag Not Found!"                    
            else:
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data        
        except TypeError as e:
            logger.error(f"Datatype error ocurred while modifying the tag:\n\n{str(e)}")
            raise e        
        except Exception as e:
            logger.error(f"An error ocurred while modifying the tag:\n\n{str(e)}")
            raise e
        
    def get_tag(self, tag_id):
        """Get the tag details
        """        
        
        try:
            data = dict()            
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for 
            # any tag regardless of the active status
            if is_courier_manager:
                tag = self.env['courier.tag.custom'].search(
                    [
                        ('id','=', int(tag_id)), '|', 
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if tag:
                    data["id"] = tag.id
                    data["name"] = tag.name
                    data["active"] = tag.active
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = data
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Tag Not Found!"
            else: 
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the tag details:\n\n{str(e)}")
            raise e
        
    def get_all_tags(self):
        """Get all the tags
        """        
        
        try:
            response_data = dict()
            all_tags = []
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for 
            # any tag regardless of the active status
            if is_courier_manager:
                tags = self.env['courier.tag.custom'].search(
                    [
                        '|',
                        ('active','=', True),
                        ('active','=', False)
                    ], order='name asc')
                
                if tags:
                    for tag in tags:
                        data = dict()                    
                        data["id"] = tag.id
                        data["name"] = tag.name
                        data["active"] = tag.active
                        
                        all_tags.append(data)
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = all_tags
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Tag Not Found!"
            else: 
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the tags:\n\n{str(e)}")
            raise e