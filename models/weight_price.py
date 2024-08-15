import logging
import requests

from datetime import datetime
from odoo import models, _, fields, api
from odoo.http import request, SessionExpiredException
from odoo.exceptions import ValidationError, UserError

logger = logging.getLogger(__name__)

class NaidashWeightPrice(models.Model):
    _inherit = "weight.price.custom"
    _order = "max_value asc"
    
    def create_the_weight_price(self, request_data):
        """Create the weight price
        """ 
        
        try:
            data = dict()
            response_data = dict()
                        
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:            
                minimum_weight = request_data.get("minimum_weight")
                maximum_weight = request_data.get("maximum_weight")
                price = request_data.get("price")
                
                if not minimum_weight:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `minimum_weight` parameter"
                    return response_data
                
                if not maximum_weight:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `maximum_weight` parameter"
                    return response_data
                
                if not price:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `price` parameter"
                    return response_data                
                                
                vals = {
                    "min_value": float(minimum_weight),
                    "max_value": float(maximum_weight),
                    "cost": price,
                }
                                
                weight_price = self.env['weight.price.custom'].create(vals)

                if weight_price:
                    data['id'] = weight_price.id
                    response_data["code"] = 201                
                    response_data["message"] = "Created successfully"
                    response_data["data"] = data
            else:
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"An error ocurred while creating the weight price:\n\n{str(e)}")
            raise e
        
    def edit_the_weight_price(self, weight_price_id, request_data):
        """Edit the weight price details
        """ 
                
        try:
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:
                weight_price = self.env['weight.price.custom'].search(
                    [
                        ('id','=', int(weight_price_id)), '|', 
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if weight_price:
                    weight_price_details = dict()
                                
                    if request_data.get("minimum_weight"):
                        weight_price_details["min_value"] = float(request_data.get("minimum_weight"))
                        
                    if request_data.get("maximum_weight"):
                        weight_price_details["max_value"] = float(request_data.get("maximum_weight"))
                        
                    if request_data.get("price"):
                        weight_price_details["cost"] = request_data.get("price")

                    if request_data.get("active"):
                        weight_price_details["active"] = request_data.get("active")
                        
                    # Update weight price details
                    if weight_price_details:
                        weight_price.write(weight_price_details)
                        response_data["code"] = 200
                        response_data["message"] = "Updated successfully"
                    else:
                        response_data["code"] = 204
                        response_data["message"] = "Nothing to update"
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Weight Price Not Found!"                    
            else:
                response_data["code"] = 403
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except TypeError as e:
            logger.error(f"Datatype error ocurred while modifying the weight price:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while modifying the weight price:\n\n{str(e)}")
            raise e
        
    def get_the_weight_price(self, weight_price_id):
        """Get the weight price details
        """        
        
        try:
            data = dict()            
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for 
            # any weight price regardless of the active status
            if is_courier_manager:
                weight_price = self.env['weight.price.custom'].search(
                    [
                        ('id','=', int(weight_price_id)), '|', 
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if weight_price:
                    data["id"] = weight_price.id
                    data["name"] = weight_price.name
                    data["minimum_weight"] = weight_price.min_value
                    data["maximum_weight"] = weight_price.max_value
                    data["price"] = weight_price.cost
                    data["active"] = weight_price.active
                                        
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = data
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Weight Price Not Found!"
            else: 
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the weight price details:\n\n{str(e)}")
            raise e
        
    def get_all_the_weight_prices(self):
        """Get all the weight prices
        """        
        
        try:
            response_data = dict()
            all_weight_prices = []
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for 
            # any weight price regardless of the active status
            if is_courier_manager:
                weight_prices = self.env['weight.price.custom'].search(
                    [
                        '|',
                        ('active','=', True),
                        ('active','=', False)
                    ])
                
                if weight_prices:
                    for weight_price in weight_prices:
                        data = dict()                    
                        data["id"] = weight_price.id
                        data["name"] = weight_price.name
                        data["minimum_weight"] = weight_price.min_value
                        data["maximum_weight"] = weight_price.max_value
                        data["price"] = weight_price.cost
                        data["active"] = weight_price.active
                        
                        all_weight_prices.append(data)
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = all_weight_prices
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Weight Price Not Found!"
            else: 
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the weight prices:\n\n{str(e)}")
            raise e