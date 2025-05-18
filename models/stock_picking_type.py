import logging
import requests
import pytz

from datetime import datetime, date, timedelta
from odoo import models, _, fields, api
from odoo.http import request, SessionExpiredException
from odoo.exceptions import ValidationError, UserError

logger = logging.getLogger(__name__)

class NaidashStockPickingType(models.Model):
    _inherit = "stock.picking.type"
    
    def create_the_stock_picking_type(self, request_data):
        """Create the stock picking type
        """ 
        
        try:
            vals = dict()
            data = dict()
            response_data = dict()
            logged_in_user = self.env.user
            search_criteria = [("company_id", "=", logged_in_user.company_id.id)]
                                    
            stock_picking_type_name = request_data.get("name")
            operation_type = request_data.get("operation_type")
            sequence_code = request_data.get("sequence_code")
            warehouse_id = request_data.get("warehouse_id")
            sequence_id = request_data.get("sequence_id")
            return_stock_picking_type_id = request_data.get("return_stock_picking_type_id")
            return_stock_location_id = request_data.get("return_stock_location_id")
            create_backorder = request_data.get("create_backorder")
            reservation_method = request_data.get("reservation_method")
            create_lot_or_serial_no = request_data.get("create_lot_or_serial_no")
            use_existing_lot_or_serial_no = request_data.get("use_existing_lot_or_serial_no")

            if not stock_picking_type_name:
                response_data["code"] = 400
                response_data["message"] = "Bad Request! Expected a name"
                return response_data

            if not operation_type:
                response_data["code"] = 400
                response_data["message"] = "Bad Request! Expected the operation type"
                return response_data
            
            if not warehouse_id:
                response_data["code"] = 400
                response_data["message"] = "Bad Request! Expected the warehouse id"
                return response_data
            
            if not sequence_id:
                response_data["code"] = 400
                response_data["message"] = "Bad Request! Expected the sequence id"
                return response_data
            
            if not sequence_code:
                response_data["code"] = 400
                response_data["message"] = "Bad Request! Expected the sequence code"
                return response_data
            
            if not create_backorder:
                response_data["code"] = 400
                response_data["message"] = "Bad Request! Specify the type of backorder"
                return response_data
            
            vals["company_id"] = logged_in_user.company_id.id
            vals["name"] = stock_picking_type_name
            vals["code"] = operation_type
            vals["sequence_code"] = sequence_code
            vals["sequence_id"] = sequence_id
            vals["create_backorder"] = create_backorder
            vals["reservation_method"] = reservation_method
            
            if create_lot_or_serial_no == True or create_lot_or_serial_no == False:
                vals["use_create_lots"] = create_lot_or_serial_no
                
            if use_existing_lot_or_serial_no == True or use_existing_lot_or_serial_no == False:
                vals["use_existing_lots"] = use_existing_lot_or_serial_no
            
            search_criteria.append(("id", "=", int(warehouse_id)))
            warehouse = self.env['stock.warehouse'].search(search_criteria)
            
            if warehouse:
                vals["warehouse_id"] = warehouse.id
            else:
                response_data["code"] = 404
                response_data["message"] = "Warehouse not found!"
                return response_data
            
            if return_stock_picking_type_id:
                return_stock_picking_type = self.env['stock.picking.type'].browse(int(return_stock_picking_type_id))
                
                if return_stock_picking_type:
                    vals["return_picking_type_id"] = return_stock_picking_type.id
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Return picking type not found!"
                    return response_data
                
            if return_stock_location_id:
                return_stock_location = self.env['stock.location'].browse(int(return_stock_location_id))
                
                if return_stock_location:
                    vals["default_location_return_id"] = return_stock_location.id
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Return location not found!"
                    return response_data
            
            stock_picking_type = self.env['stock.picking.type'].create(vals)
            
            if stock_picking_type:
                data['id'] = stock_picking_type.id
                response_data["code"] = 201
                response_data["message"] = "Created successfully"
                response_data["data"] = data
            else:
                response_data["code"] = 204
                response_data["message"] = "Failed to create the stock picking type"
                return response_data
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while creating the stock picking type:\n\n{str(e)}")
            raise e
        
    def edit_the_stock_picking_type(self, stock_picking_type_id, request_data):
        """Edit the stock picking type details
        """ 
                
        try:
            response_data = dict()
            stock_picking_type = self.env['stock.picking.type'].browse(int(stock_picking_type_id))
            
            if stock_picking_type:
                stock_picking_type_details = dict()
                                
                if request_data.get("name"):
                    stock_picking_type_details["name"] = request_data.get("name")

                if request_data.get("operation_type"):
                    stock_picking_type_details["code"] = request_data.get("operation_type")
                    
                if request_data.get("sequence_code"):
                    stock_picking_type_details["sequence_code"] = request_data.get("sequence_code")
                    
                if request_data.get("create_backorder"):
                    stock_picking_type_details["create_backorder"] = request_data.get("create_backorder")
                    
                if request_data.get("reservation_method"):
                    stock_picking_type_details["reservation_method"] = request_data.get("reservation_method")                    
                    
                if request_data.get("active") == True or request_data.get("active") == False:
                    stock_picking_type_details["active"] = request_data.get("active")
                    
                if request_data.get("create_lot_or_serial_no"):
                    stock_picking_type_details["use_create_lots"] = request_data.get("create_lot_or_serial_no")
                    
                if request_data.get("use_existing_lot_or_serial_no"):
                    stock_picking_type_details["use_existing_lots"] = request_data.get("use_existing_lot_or_serial_no")
                                    
                if request_data.get("warehouse_id"):
                    warehouse_id = request_data.get("warehouse_id")
                    warehouse = self.env['stock.warehouse'].browse(int(warehouse_id))
                    
                    if warehouse:
                        stock_picking_type_details["warehouse_id"] = warehouse.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Warehouse not found!"
                        return response_data
                    
                if request_data.get("sequence_id"):
                    sequence_id = request_data.get("sequence_id")
                    sequence = self.env['ir.sequence'].browse(int(sequence_id))
                    
                    if sequence:
                        stock_picking_type_details["sequence_id"] = sequence.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Sequence not found!"
                        return response_data
                    
                if request_data.get("return_stock_picking_type_id"):
                    return_stock_picking_type_id = request_data.get("return_stock_picking_type_id")
                    return_stock_picking_type = self.env['stock.picking.type'].browse(int(return_stock_picking_type_id))
                    
                    if return_stock_picking_type:
                        stock_picking_type_details["return_picking_type_id"] = return_stock_picking_type.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Return picking type not found!"
                        return response_data
                    
                if request_data.get("return_stock_location_id"):
                    return_stock_location_id = request_data.get("return_stock_location_id")                   
                    return_stock_location = self.env['stock.location'].browse(int(return_stock_location_id))
                    
                    if return_stock_location:
                        stock_picking_type_details["default_location_return_id"] = return_stock_location.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Return location not found!"
                        return response_data
                                        
                # Update stock picking type details
                if stock_picking_type_details:
                    stock_picking_type.write(stock_picking_type_details)
                    response_data["code"] = 200
                    response_data["message"] = "Updated successfully"
                else:
                    response_data["code"] = 204
                    response_data["message"] = "Nothing to update"
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock picking type not found!"                    
            
            return response_data
        except TypeError as e:
            logger.error(f"Datatype error ocurred while modifying the stock picking type details:\n\n{str(e)}")
            raise e
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while modifying the stock picking type details:\n\n{str(e)}")
            raise e
        
    def get_the_stock_picking_type(self, stock_picking_type_id):
        """Get the stock picking type details
        """        
        
        try:
            data = dict()
            response_data = dict()
            logged_in_user = self.env.user
            
            stock_picking_type = self.env['stock.picking.type'].browse(int(stock_picking_type_id))
            
            if stock_picking_type:
                data["id"] = stock_picking_type.id
                data["name"] = stock_picking_type.name
                data["operation_type"] = stock_picking_type.code
                data["create_backorder"] = stock_picking_type.create_backorder
                data["reservation_method"] = stock_picking_type.reservation_method
                data["create_lot_or_serial_no"] = stock_picking_type.use_create_lots
                data["use_existing_lot_or_serial_no"] = stock_picking_type.use_existing_lots
                data["sequence_code"] = stock_picking_type.sequence_code
                data["sequence"] = {"id": stock_picking_type.sequence_id.id, "name": stock_picking_type.sequence_id.name} if stock_picking_type.sequence_id else {}
                data["warehouse"] = {"id": stock_picking_type.warehouse_id.id, "name": stock_picking_type.warehouse_id.name} if stock_picking_type.warehouse_id else {}
                data["company"] = {"id": stock_picking_type.company_id.id, "name": stock_picking_type.company_id.name} if stock_picking_type.company_id else {}
                data["return_stock_picking_type"] = {"id": stock_picking_type.return_picking_type_id.id, "name": stock_picking_type.return_picking_type_id.name} if stock_picking_type.return_picking_type_id else {}
                data["return_stock_location"] = {"id": stock_picking_type.default_location_return_id.id, "name": stock_picking_type.default_location_return_id.name} if stock_picking_type.default_location_return_id else {}
                data["source_stock_location"] = {"id": stock_picking_type.default_location_src_id.id, "name": stock_picking_type.default_location_src_id.name} if stock_picking_type.default_location_src_id else {}
                data["destination_stock_location"] = {"id": stock_picking_type.default_location_dest_id.id, "name": stock_picking_type.default_location_dest_id.name} if stock_picking_type.default_location_dest_id else {}
                                    
                response_data["code"] = 200
                response_data["message"] = "Success"
                response_data["data"] = data
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock picking type not found!"
            
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the stock picking type details:\n\n{str(e)}")
            raise e
        
    def get_all_the_stock_picking_types(self, query_params):
        """Get all the stock picking types 
        """        
        
        try:
            response_data = dict()
            all_stock_picking_types = []
            logged_in_user = self.env.user
            search_criteria = [("company_id", "=", logged_in_user.company_id.id)]
            
            if query_params.get("operation_type"):
                operation_type = query_params.get("operation_type")
                search_criteria.append(
                    ("code", "=", operation_type)
                )
                
            if query_params.get("warehouse_id"):
                warehouse_id = query_params.get("warehouse_id")
                search_criteria.append(
                    ('warehouse_id', '=', int(warehouse_id))
                )
            
            stock_picking_types = self.env['stock.picking.type'].search(search_criteria, order='name asc')
            
            if stock_picking_types:
                for stock_picking_type in stock_picking_types:
                    data = dict()
                    data["id"] = stock_picking_type.id
                    data["name"] = stock_picking_type.name
                    data["operation_type"] = stock_picking_type.code
                    data["create_backorder"] = stock_picking_type.create_backorder
                    data["reservation_method"] = stock_picking_type.reservation_method
                    data["create_lot_or_serial_no"] = stock_picking_type.use_create_lots
                    data["use_existing_lot_or_serial_no"] = stock_picking_type.use_existing_lots
                    data["sequence_code"] = stock_picking_type.sequence_code
                    data["sequence"] = {"id": stock_picking_type.sequence_id.id, "name": stock_picking_type.sequence_id.name} if stock_picking_type.sequence_id else {}
                    data["warehouse"] = {"id": stock_picking_type.warehouse_id.id, "name": stock_picking_type.warehouse_id.name} if stock_picking_type.warehouse_id else {}
                    data["company"] = {"id": stock_picking_type.company_id.id, "name": stock_picking_type.company_id.name} if stock_picking_type.company_id else {}
                    data["return_stock_picking_type"] = {"id": stock_picking_type.return_picking_type_id.id, "name": stock_picking_type.return_picking_type_id.name} if stock_picking_type.return_picking_type_id else {}
                    data["return_stock_location"] = {"id": stock_picking_type.default_location_return_id.id, "name": stock_picking_type.default_location_return_id.name} if stock_picking_type.default_location_return_id else {}
                    data["source_stock_location"] = {"id": stock_picking_type.default_location_src_id.id, "name": stock_picking_type.default_location_src_id.name} if stock_picking_type.default_location_src_id else {}
                    data["destination_stock_location"] = {"id": stock_picking_type.default_location_dest_id.id, "name": stock_picking_type.default_location_dest_id.name} if stock_picking_type.default_location_dest_id else {}
                    
                    all_stock_picking_types.append(data)
                
                response_data["code"] = 200
                response_data["message"] = "Success"
                response_data["data"] = all_stock_picking_types
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock picking type not found!"
            
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the stock picking types:\n\n{str(e)}")
            raise e
