import logging
import requests

from datetime import datetime
from odoo import models, _, fields, api
from odoo.http import request, SessionExpiredException
from odoo.exceptions import ValidationError, UserError

logger = logging.getLogger(__name__)

class NaidashDistancePrice(models.Model):
    _inherit = "distance.price.custom"
    _order = "max_value asc"
    
    def create_the_distance_price(self, request_data):
        """Create the distance price
        """ 
        
        try:
            data = dict()
            response_data = dict()
                        
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:            
                minimum_distance = request_data.get("minimum_distance")
                maximum_distance = request_data.get("maximum_distance")
                product_id = request_data.get("product_id")                
                price = request_data.get("price")
                
                if not minimum_distance:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `minimum_distance` parameter"
                    return response_data
                
                if not maximum_distance:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `maximum_distance` parameter"
                    return response_data
                
                if not product_id:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `product_id` parameter"
                    return response_data                
                
                if not price:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `price` parameter"
                    return response_data                
                                
                vals = {
                    "min_value": int(minimum_distance),
                    "max_value": int(maximum_distance),
                    "product_id": int(product_id),
                    "cost": price,
                }
                                
                distance_price = self.env['distance.price.custom'].create(vals)

                if distance_price:
                    data['id'] = distance_price.id
                    response_data["code"] = 201                
                    response_data["message"] = "Created successfully"
                    response_data["data"] = data
            else:
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"An error ocurred while creating the distance price:\n\n{str(e)}")
            raise e
        
    def edit_the_distance_price(self, distance_price_id, request_data):
        """Edit the distance price details
        """ 
                
        try:
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:
                distance_price = self.env['distance.price.custom'].search(
                    [
                        ('id','=', int(distance_price_id)), '|', 
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if distance_price:
                    distance_price_details = dict()
                                
                    if request_data.get("minimum_distance"):
                        distance_price_details["min_value"] = int(request_data.get("minimum_distance"))
                        
                    if request_data.get("maximum_distance"):
                        distance_price_details["max_value"] = int(request_data.get("maximum_distance"))
                        
                    if request_data.get("product_id"):
                        distance_price_details["product_id"] = int(request_data.get("product_id"))                        
                        
                    if request_data.get("price"):
                        distance_price_details["cost"] = request_data.get("price")

                    if request_data.get("active"):
                        distance_price_details["active"] = request_data.get("active")
                        
                    # Update distance price details
                    if distance_price_details:
                        distance_price.write(distance_price_details)
                        response_data["code"] = 200
                        response_data["message"] = "Updated successfully"
                    else:
                        response_data["code"] = 204
                        response_data["message"] = "Nothing to update"
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Distance Price Not Found!"                    
            else:
                response_data["code"] = 403
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except TypeError as e:
            logger.error(f"Datatype error ocurred while modifying the distance price:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while modifying the distance price:\n\n{str(e)}")
            raise e
        
    def get_the_distance_price(self, distance_price_id):
        """Get the distance price details
        """        
        
        try:
            data = dict()            
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for 
            # any distance price regardless of the active status
            if is_courier_manager:
                distance_price = self.env['distance.price.custom'].search(
                    [
                        ('id','=', int(distance_price_id)), '|', 
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if distance_price:
                    data["id"] = distance_price.id
                    data["name"] = distance_price.name
                    data["minimum_distance"] = distance_price.min_value
                    data["maximum_distance"] = distance_price.max_value
                    data["price"] = distance_price.cost
                    data["active"] = distance_price.active
                    data["product"] = {"id": distance_price.product_id.id, "name": distance_price.product_id.name} if distance_price.product_id else {}
                                        
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = data
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Distance Price Not Found!"
            else: 
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the distance price details:\n\n{str(e)}")
            raise e
        
    def get_all_the_distance_prices(self):
        """Get all the distance prices
        """        
        
        try:
            response_data = dict()
            all_distance_prices = []
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for 
            # any distance price regardless of the active status
            if is_courier_manager:
                distance_prices = self.env['distance.price.custom'].search(
                    [
                        '|',
                        ('active','=', True),
                        ('active','=', False)
                    ])
                
                if distance_prices:
                    for distance_price in distance_prices:
                        data = dict()                    
                        data["id"] = distance_price.id
                        data["name"] = distance_price.name
                        data["minimum_distance"] = distance_price.min_value
                        data["maximum_distance"] = distance_price.max_value
                        data["price"] = distance_price.cost
                        data["active"] = distance_price.active
                        data["product"] = {"id": distance_price.product_id.id, "name": distance_price.product_id.name} if distance_price.product_id else {}
                        
                        all_distance_prices.append(data)
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = all_distance_prices
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Distance Price Not Found!"
            else: 
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the distance prices:\n\n{str(e)}")
            raise e