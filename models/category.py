import logging
import requests

from datetime import datetime
from odoo import models, _, fields, api
from odoo.http import request, SessionExpiredException
from odoo.exceptions import ValidationError, UserError

logger = logging.getLogger(__name__)

class NaidashCategory(models.Model):
    _inherit = "courier.category.custom"
    _order = "name asc"
    
    def create_category(self, request_data):
        """Create the category
        """ 
        
        try:
            data = dict()
            response_data = dict()
            param_values = ["", None]            
            
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:            
                category_name = request_data.get("name")
                
                if category_name in param_values:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `name` parameter"
                    return response_data
                
                category_name = (request_data.get("name")).strip()                
                category = self.env['courier.category.custom'].create({"name": category_name})

                if category:
                    data['id'] = category.id
                    response_data["code"] = 201                
                    response_data["message"] = "Created successfully"
                    response_data["data"] = data
            else:
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"An error ocurred while creating the category:\n\n{str(e)}")
            raise e
        
    def edit_category(self, category_id, request_data):
        """Edit the category details
        """ 
                
        try:
            response_data = dict()
            search_param_values = ["", None]
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:
                category = self.env['courier.category.custom'].search(
                    [
                        ('id','=', int(category_id)), '|', 
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if category:
                    category_details = dict()
                                
                    if request_data.get("name") not in search_param_values:
                        category_details["name"] = (request_data.get("name")).strip()

                    if request_data.get("active") not in search_param_values:
                        category_details["active"] = request_data.get("active")
                        
                    # Update category details
                    if category_details:
                        category.write(category_details)
                        response_data["code"] = 200
                        response_data["message"] = "Updated successfully"
                    else:
                        response_data["code"] = 204
                        response_data["message"] = "Nothing to update"
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Category Not Found!"                    
            else:
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data        
        except TypeError as e:
            logger.error(f"Datatype error ocurred while modifying the category:\n\n{str(e)}")
            raise e        
        except Exception as e:
            logger.error(f"An error ocurred while modifying the category:\n\n{str(e)}")
            raise e
        
    def get_category(self, category_id):
        """Get the category details
        """        
        
        try:
            data = dict()            
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for 
            # any category regardless of the active status
            if is_courier_manager:
                category = self.env['courier.category.custom'].search(
                    [
                        ('id','=', int(category_id)), '|', 
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if category:
                    data["id"] = category.id
                    data["name"] = category.name
                    data["active"] = category.active
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = data
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Category Not Found!"
            else: 
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the category details:\n\n{str(e)}")
            raise e
        
    def get_all_categories(self):
        """Get all the categories
        """        
        
        try:
            response_data = dict()
            all_categories = []
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for 
            # any category regardless of the active status
            if is_courier_manager:
                categories = self.env['courier.category.custom'].search(
                    [
                        '|',
                        ('active','=', True),
                        ('active','=', False)
                    ], order='name asc')
                
                if categories:
                    for category in categories:
                        data = dict()                    
                        data["id"] = category.id
                        data["name"] = category.name
                        data["active"] = category.active
                        
                        all_categories.append(data)
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = all_categories
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Category Not Found!"
            else: 
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the categories:\n\n{str(e)}")
            raise e