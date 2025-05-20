import logging
import requests
import pytz

from datetime import datetime, date, timedelta
from odoo import models, _, fields, api
from odoo.http import request, SessionExpiredException
from odoo.exceptions import ValidationError, UserError

logger = logging.getLogger(__name__)

class NaidashStockLocation(models.Model):
    _inherit = "stock.location"
    
    def create_the_stock_location(self, request_data):
        """Create the stock location
        """ 
        
        try:
            vals = dict()
            data = dict()
            response_data = dict()
            logged_in_user = self.env.user
                                    
            stock_location_name = request_data.get("name")
            location_type = request_data.get("location_type")
            parent_stock_location_id = request_data.get("parent_stock_location_id")
            inventory_frequency = request_data.get("inventory_frequency")
            is_scrap_location = request_data.get("is_scrap_location")
            is_return_location = request_data.get("is_return_location")
            is_replenish_location = request_data.get("is_replenish_location")

            if not stock_location_name:
                response_data["code"] = 400
                response_data["message"] = "Bad Request! Expected a name"
                return response_data

            if not location_type:
                response_data["code"] = 400
                response_data["message"] = "Bad Request! Expected the location type"
                return response_data
                        
            vals["company_id"] = logged_in_user.company_id.id
            vals["name"] = stock_location_name
            vals["usage"] = location_type
            
            if inventory_frequency:
                vals["cyclic_inventory_frequency"] = int(inventory_frequency)
            
            if is_scrap_location == True or is_scrap_location == False:
                vals["scrap_location"] = is_scrap_location
                
            if is_return_location == True or is_return_location == False:
                vals["return_location"] = is_return_location
                
            if is_replenish_location == True or is_replenish_location == False:
                vals["replenish_location"] = is_replenish_location
            
            if parent_stock_location_id:
                stock_location = self.env['stock.location'].search(
                    [
                        ("id", "=", int(parent_stock_location_id)),
                        ("company_id", "=", logged_in_user.company_id.id)
                    ]
                )
                
                if stock_location:
                    vals["location_id"] = stock_location.id
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Stock location not found!"
                    return response_data
            
            stock_location = self.env['stock.location'].create(vals)
            
            if stock_location:
                data['id'] = stock_location.id
                response_data["code"] = 201
                response_data["message"] = "Created successfully"
                response_data["data"] = data
            else:
                response_data["code"] = 204
                response_data["message"] = "Failed to create the stock location"
                return response_data
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while creating the stock location:\n\n{str(e)}")
            raise e
        
    def edit_the_stock_location(self, stock_location_id, request_data):
        """Edit the stock location details
        """ 
                
        try:
            response_data = dict()
            logged_in_user = self.env.user
            
            stock_location = self.env['stock.location'].search(
                [
                    ("id", "=", int(stock_location_id)),
                    ("company_id", "=", logged_in_user.company_id.id),
                    ("active", "in", [True, False])
                ]
            )
            
            if stock_location:
                stock_location_details = dict()
                                
                if request_data.get("name"):
                    stock_location_details["name"] = request_data.get("name")

                if request_data.get("location_type"):
                    stock_location_details["usage"] = request_data.get("location_type")
                    
                if request_data.get("inventory_frequency"):
                    stock_location_details["cyclic_inventory_frequency"] = int(request_data.get("inventory_frequency"))
                    
                if request_data.get("is_scrap_location")  == True or request_data.get("is_scrap_location") == False:
                    stock_location_details["scrap_location"] = request_data.get("is_scrap_location")
                    
                if request_data.get("is_return_location") == True or request_data.get("is_return_location") == False:
                    stock_location_details["return_location"] = request_data.get("is_return_location")
                    
                if request_data.get("is_replenish_location") == True or request_data.get("is_replenish_location") == False:
                    stock_location_details["replenish_location"] = request_data.get("is_replenish_location")
                                                        
                if request_data.get("active") == True or request_data.get("active") == False:
                    stock_location_details["active"] = request_data.get("active")
                    
                if request_data.get("parent_stock_location_id"):
                    parent_stock_location_id = request_data.get("parent_stock_location_id")
                    
                    parent_stock_location = self.env['stock.location'].search(
                        [
                            ("id", "=", int(parent_stock_location_id)),
                            ("company_id", "=", logged_in_user.company_id.id),
                            ("active", "in", [True, False])
                        ]
                    )
                    
                    if parent_stock_location:
                        stock_location_details["location_id"] = parent_stock_location.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Parent stock location not found!"
                        return response_data
                                                            
                # Update stock location details
                if stock_location_details:
                    stock_location.write(stock_location_details)
                    response_data["code"] = 200
                    response_data["message"] = "Updated successfully"
                else:
                    response_data["code"] = 204
                    response_data["message"] = "Nothing to update"
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock location not found!"                    
            
            return response_data
        except TypeError as e:
            logger.error(f"Datatype error ocurred while modifying the stock location details:\n\n{str(e)}")
            raise e
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while modifying the stock location details:\n\n{str(e)}")
            raise e
        
    def get_the_stock_location(self, stock_location_id):
        """Get the stock location details
        """        
        
        try:
            data = dict()
            response_data = dict()
            logged_in_user = self.env.user
            
            stock_location = self.env['stock.location'].search(
                [
                    ("id", "=", int(stock_location_id)),
                    ("company_id", "=", logged_in_user.company_id.id),
                    ("active", "in", [True, False])
                ]
            )
                        
            if stock_location:
                data["id"] = stock_location.id
                data["name"] = stock_location.name
                data["location_type"] = stock_location.usage
                data["inventory_frequency"] = stock_location.cyclic_inventory_frequency
                data["is_scrap_location"] = stock_location.scrap_location
                data["is_return_location"] = stock_location.return_location
                data["is_replenish_location"] = stock_location.replenish_location
                data["active"] = stock_location.active
                data["last_inventory_date"] = (stock_location.last_inventory_date).strftime("%Y-%m-%d") if stock_location.last_inventory_date else ""
                data["next_inventory_date"] = (stock_location.next_inventory_date).strftime("%Y-%m-%d") if stock_location.next_inventory_date else ""
                data["parent_stock_location"] = {"id": stock_location.location_id.id, "name": stock_location.location_id.name} if stock_location.location_id else {}
                data["warehouse"] = {"id": stock_location.warehouse_id.id, "name": stock_location.warehouse_id.name} if stock_location.warehouse_id else {}
                data["company"] = {"id": stock_location.company_id.id, "name": stock_location.company_id.name} if stock_location.company_id else {}
                data["stock_quantities"] = [
                    {
                        "id": item.id, 
                        "quantity_on_hand": item.quantity,
                        "quantity_available": item.available_quantity,
                        "value": item.value,
                        "stock_location": {"id": item.location_id.id, "name": item.location_id.name} if item.location_id else {},
                        "stock_lot": {"id": item.lot_id.id, "name": item.lot_id.name} if item.lot_id else {},
                        "product": {"id": item.product_id.id, "name": item.product_id.name} if item.product_id else {},
                        "uom": {"id": item.product_uom_id.id, "name": item.product_uom_id.name} if item.product_uom_id else {},
                        "company": {"id": item.company_id.id, "name": item.company_id.name} if item.company_id else {}
                    } for item in stock_location.quant_ids
                ] if stock_location.quant_ids else []
                                    
                response_data["code"] = 200
                response_data["message"] = "Success"
                response_data["data"] = data
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock location not found!"
            
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the stock location details:\n\n{str(e)}")
            raise e
        
    def get_all_the_stock_locations(self, query_params):
        """Get all the stock locations 
        """        
        
        try:
            response_data = dict()
            all_stock_locations = []
            logged_in_user = self.env.user
            search_criteria = [("company_id", "=", logged_in_user.company_id.id)]
            
            if query_params.get("location_type"):
                location_type = query_params.get("location_type")
                search_criteria.append(
                    ("usage", "=", location_type)
                )
                
            if query_params.get("warehouse_id"):
                warehouse_id = query_params.get("warehouse_id")
                search_criteria.append(
                    ('warehouse_id', '=', int(warehouse_id))
                )
            
            if query_params.get("parent_stock_location_id"):
                parent_stock_location_id = query_params.get("parent_stock_location_id")
                search_criteria.append(
                    ('location_id', '=', int(parent_stock_location_id))
                )
                
            if query_params.get("active") == True or query_params.get("active") == False:
                is_active = query_params.get("active")
                search_criteria.append(
                    ("active", "=", is_active)
                )
            
            stock_locations = self.env['stock.location'].search(search_criteria, order='name asc')
            
            if stock_locations:
                for stock_location in stock_locations:
                    data = dict()
                    data["id"] = stock_location.id
                    data["name"] = stock_location.name
                    data["location_type"] = stock_location.usage
                    data["inventory_frequency"] = stock_location.cyclic_inventory_frequency
                    data["is_scrap_location"] = stock_location.scrap_location
                    data["is_return_location"] = stock_location.return_location
                    data["is_replenish_location"] = stock_location.replenish_location
                    data["active"] = stock_location.active
                    data["last_inventory_date"] = (stock_location.last_inventory_date).strftime("%Y-%m-%d") if stock_location.last_inventory_date else ""
                    data["next_inventory_date"] = (stock_location.next_inventory_date).strftime("%Y-%m-%d") if stock_location.next_inventory_date else ""
                    data["parent_stock_location"] = {"id": stock_location.location_id.id, "name": stock_location.location_id.name} if stock_location.location_id else {}
                    data["warehouse"] = {"id": stock_location.warehouse_id.id, "name": stock_location.warehouse_id.name} if stock_location.warehouse_id else {}
                    data["company"] = {"id": stock_location.company_id.id, "name": stock_location.company_id.name} if stock_location.company_id else {}
                    data["stock_quantities"] = [
                        {
                            "id": item.id, 
                            "quantity_on_hand": item.quantity,
                            "quantity_available": item.available_quantity,
                            "value": item.value,
                            "stock_location": {"id": item.location_id.id, "name": item.location_id.name} if item.location_id else {},
                            "stock_lot": {"id": item.lot_id.id, "name": item.lot_id.name} if item.lot_id else {},
                            "product": {"id": item.product_id.id, "name": item.product_id.name} if item.product_id else {},
                            "uom": {"id": item.product_uom_id.id, "name": item.product_uom_id.name} if item.product_uom_id else {},
                            "company": {"id": item.company_id.id, "name": item.company_id.name} if item.company_id else {}
                        } for item in stock_location.quant_ids
                    ] if stock_location.quant_ids else []
                    
                    all_stock_locations.append(data)
                
                response_data["code"] = 200
                response_data["message"] = "Success"
                response_data["data"] = all_stock_locations
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock location not found!"
            
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the stock locations:\n\n{str(e)}")
            raise e
