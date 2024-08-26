import logging
import requests

from datetime import datetime
from odoo import models, _, fields, api
from odoo.http import request, SessionExpiredException
from odoo.exceptions import ValidationError, UserError

logger = logging.getLogger(__name__)

class NaidashDimensionPrice(models.Model):
    _inherit = "dimension.price.custom"
    _order = "volumetric_weight asc"
    
    def create_the_dimension_price(self, request_data):
        """Create the dimension price
        """ 
        
        try:
            data = dict()
            response_data = dict()
                        
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:            
                length = request_data.get("length")
                width = request_data.get("width")
                height = request_data.get("height")
                price = request_data.get("price")
                
                if not length:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `length` parameter"
                    return response_data
                
                if not width:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `width` parameter"
                    return response_data
                
                if not height:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `height` parameter"
                    return response_data                
                
                if not price:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `price` parameter"
                    return response_data                
                                
                vals = {
                    "length": int(length),
                    "width": int(width),
                    "height": int(height),
                    "cost": price,
                }
                                
                dimension_price = self.env['dimension.price.custom'].create(vals)

                if dimension_price:
                    data['id'] = dimension_price.id
                    response_data["code"] = 201                
                    response_data["message"] = "Created successfully"
                    response_data["data"] = data
            else:
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"An error ocurred while creating the dimension price:\n\n{str(e)}")
            raise e
        
    def edit_the_dimension_price(self, dimension_price_id, request_data):
        """Edit the dimension price details
        """ 
                
        try:
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:
                dimension_price = self.env['dimension.price.custom'].search(
                    [
                        ('id','=', int(dimension_price_id)), '|', 
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if dimension_price:
                    dimension_price_details = dict()
                                
                    if request_data.get("length"):
                        dimension_price_details["length"] = int(request_data.get("length"))
                        
                    if request_data.get("width"):
                        dimension_price_details["width"] = int(request_data.get("width"))
                        
                    if request_data.get("height"):
                        dimension_price_details["height"] = int(request_data.get("height"))                        
                        
                    if request_data.get("price"):
                        dimension_price_details["cost"] = request_data.get("price")

                    if request_data.get("active"):
                        dimension_price_details["active"] = request_data.get("active")
                        
                    # Update dimension price details
                    if dimension_price_details:
                        dimension_price.write(dimension_price_details)
                        response_data["code"] = 200
                        response_data["message"] = "Updated successfully"
                    else:
                        response_data["code"] = 204
                        response_data["message"] = "Nothing to update"
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Dimension Price Not Found!"                    
            else:
                response_data["code"] = 403
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except TypeError as e:
            logger.error(f"Datatype error ocurred while modifying the dimension price:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while modifying the dimension price:\n\n{str(e)}")
            raise e
        
    def get_the_dimension_price(self, dimension_price_id):
        """Get the dimension price details
        """        
        
        try:
            data = dict()            
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for 
            # any dimension price regardless of the active status
            if is_courier_manager:
                dimension_price = self.env['dimension.price.custom'].search(
                    [
                        ('id','=', int(dimension_price_id)), '|', 
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if dimension_price:
                    data["id"] = dimension_price.id
                    data["name"] = dimension_price.name
                    data["length"] = dimension_price.length
                    data["width"] = dimension_price.width
                    data["height"] = dimension_price.height
                    data["volumetric_weight"] = dimension_price.volumetric_weight
                    data["price"] = dimension_price.cost
                    data["active"] = dimension_price.active
                                        
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = data
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Dimension Price Not Found!"
            else: 
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the dimension price details:\n\n{str(e)}")
            raise e
        
    def get_all_the_dimension_prices(self):
        """Get all the dimension prices
        """        
        
        try:
            response_data = dict()
            all_dimension_prices = []
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for 
            # any dimension price regardless of the active status
            if is_courier_manager:
                dimension_prices = self.env['dimension.price.custom'].search(
                    [
                        '|',
                        ('active','=', True),
                        ('active','=', False)
                    ])
                
                if dimension_prices:
                    for dimension_price in dimension_prices:
                        data = dict()                    
                        data["id"] = dimension_price.id
                        data["name"] = dimension_price.name
                        data["length"] = dimension_price.length
                        data["width"] = dimension_price.width
                        data["height"] = dimension_price.height
                        data["volumetric_weight"] = dimension_price.volumetric_weight
                        data["price"] = dimension_price.cost
                        data["active"] = dimension_price.active
                        
                        all_dimension_prices.append(data)
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = all_dimension_prices
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Dimension Price Not Found!"
            else: 
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the dimension prices:\n\n{str(e)}")
            raise e