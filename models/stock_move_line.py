import logging
import requests
import pytz

from datetime import datetime, date, timedelta
from odoo import models, _, fields, api
from odoo.http import request, SessionExpiredException
from odoo.exceptions import ValidationError, UserError

logger = logging.getLogger(__name__)

class NaidashStockMoveLine(models.Model):
    _inherit = "stock.move.line"
    
    def create_the_stock_move_line(self, request_data):
        """Create the stock move line
        """ 
        
        try:
            vals = dict()
            data = dict()
            response_data = dict(code=204,message="Failed to create the stock move line")
            items_to_receive = []
            logged_in_user = self.env.user            
                                    
            partner_id = request_data.get("partner_id")
            stock_move_line_type_id = request_data.get("stock_move_line_type_id")
            assigned_user_id = request_data.get("assigned_user_id")
            stock_moves = request_data.get("stock_moves")
            # procurement_group_id = request_data.get("procurement_group_id")
            
            vals["scheduled_date"] = request_data.get("date_scheduled")
            vals["note"] = request_data.get("notes")
            vals["origin"] = request_data.get("origin")
            
            if not partner_id:
                response_data["code"] = 400
                response_data["message"] = "Bad Request! Expected the partner's id"
                return response_data

            if not stock_move_line_type_id:
                response_data["code"] = 400
                response_data["message"] = "Bad Request! Expected the stock move line type id"
                return response_data
            
            if not stock_moves:
                response_data["code"] = 400
                response_data["message"] = "Bad Request! Add the items to be received, delivered or transferred"
                return response_data
                            
            if isinstance(stock_moves, list) == False:
                response_data["code"] = 422
                response_data["message"] = "Unprocessable Content! Expected a list of objects in `stock_moves`"
                return response_data
            
            if assigned_user_id:
                user = self.env['res.users'].search(
                    [
                        ('id', '=', int(assigned_user_id)),
                        ('company_id', '=', logged_in_user.company_id.id)
                    ]
                )
                
                if user:
                    vals["user_id"] = user.id
                else:
                    response_data["code"] = 404
                    response_data["message"] = "User not found!"
                    return response_data                
            
            partner = self.env['res.partner'].browse(int(partner_id))
            stock_move_line_type = self.env['stock.picking.type'].search(
                [
                    ("id", "=", int(stock_move_line_type_id)),
                    ("company_id", "=", logged_in_user.company_id.id)
                ]
            )
            
            if partner:
                vals["partner_id"] = partner.id
            else:
                response_data["code"] = 404
                response_data["message"] = "Partner not found!"
                return response_data                
            
            if stock_move_line_type:
                vals["picking_type_id"] = stock_move_line_type.id               
            else:
                response_data["code"] = 404
                response_data["message"] = "Operation type not found!"
                return response_data
            
            for item in stock_moves:
                stock_move = dict()
                product_id = item.get("product_id")
                
                if product_id:
                    product = self.env['product.product'].search(
                        [
                            ('id', '=', int(product_id)),
                            ('detailed_type', 'in', ['product', 'consu'])
                        ]
                    )
                    
                    if product:
                        stock_move["name"] = product.name,
                        stock_move["product_id"] = product.id
                        stock_move["description_picking"] = product.name
                        stock_move["product_uom_qty"] = float(item.get("quantity")) if float(item.get("quantity")) > 0 else 1
                        #  stock_move["lot_ids"]
                        
                        if stock_move_line_type.default_location_src_id:
                            stock_move["location_id"] = stock_move_line_type.default_location_src_id.id
                        elif partner.property_stock_supplier:
                            stock_move["location_id"] = partner.property_stock_supplier.id
                        else:
                            stock_move["location_id"] = self.env['stock.warehouse']._get_partner_locations()

                        if stock_move_line_type.default_location_dest_id:
                            stock_move["location_dest_id"] = stock_move_line_type.default_location_dest_id.id
                        elif partner.property_stock_customer:
                            stock_move["location_dest_id"] = partner.property_stock_customer.id
                        else:
                            stock_move["location_dest_id"] = self.env['stock.warehouse']._get_partner_locations()
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Product not found!"
                        return response_data                            
                            
                if stock_move:                        
                    items_to_receive.append((0, 0, stock_move))
                    
            if items_to_receive:
                vals["move_ids_without_package"] = items_to_receive
            
                stock_move_line = self.env['stock.picking'].create(vals)
                
                if stock_move_line:
                    data['id'] = stock_move_line.id
                    response_data["code"] = 201
                    response_data["message"] = "Created successfully"
                    response_data["data"] = data
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while creating the stock move line details:\n\n{str(e)}")
            raise e
        
    def edit_the_stock_move_line(self, stock_move_line_id, request_data):
        """Edit the stock move line details
        """ 
                
        try:
            response_data = dict()
            stock_moves_list = []
            logged_in_user = self.env.user
            stock_moves = request_data.get("stock_moves")
            stock_move_line_type = self.env['stock.picking.type']
            partner = self.env['res.partner']
            
            stock_move_line = self.env['stock.picking'].search(
                [
                    ("id", "=", int(stock_move_line_id)),
                    ("company_id", "=", logged_in_user.company_id.id)
                ]
            )
            
            if stock_move_line:
                stock_move_line_details = dict()
                
                if request_data.get("date_scheduled"):
                    stock_move_line_details["scheduled_date"] = request_data.get("date_scheduled")

                if request_data.get("origin"):
                    stock_move_line_details["origin"] = request_data.get("origin")
                    
                if request_data.get("notes"):
                    stock_move_line_details["note"] = request_data.get("notes")
                                    
                if request_data.get("assigned_user_id"):
                    assigned_user_id = request_data.get("assigned_user_id")
                    user = self.env['res.users'].search(
                        [
                            ('id', '=', int(assigned_user_id)),
                            ('company_id', '=', logged_in_user.company_id.id)
                        ]
                    )
                    
                    if user:
                        stock_move_line_details["user_id"] = user.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "User not found!"
                        return response_data
                
                if request_data.get("partner_id"):
                    partner_id = request_data.get("partner_id")
                    partner = partner.browse(int(partner_id))
                    
                    if partner:
                        stock_move_line_details["partner_id"] = partner.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Partner not found!"
                        return response_data
                    
                if request_data.get("stock_move_line_type_id"):
                    stock_move_line_type_id = request_data.get("stock_move_line_type_id")                    
                    stock_move_line_type = stock_move_line_type.search(
                        [
                            ("id", "=", int(stock_move_line_type_id)),
                            ("company_id", "=", logged_in_user.company_id.id)
                        ]
                    )
                                        
                    if stock_move_line_type:
                        stock_move_line_details["picking_type_id"] = stock_move_line_type.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Operation type not found!"
                        return response_data
                    
                if stock_moves and isinstance(stock_moves, list):
                    for stock_move in stock_moves:
                        stock_move_to_update = dict()
                        stock_move_to_create = dict()
                        stock_move_id = stock_move.get("id")
                        product_id = stock_move.get("product_id")
                        
                        if product_id:
                            product = self.env['product.product'].search(
                                [
                                    ('id', '=', int(product_id)),
                                    ('detailed_type', 'in', ['product', 'consu'])
                                ]
                            )
                            
                            if product and not stock_move_id:
                                # If the product exists and the stock_move_id is not present, we will create a new stock move
                                stock_move_to_create["name"] = product.name
                                stock_move_to_create["product_id"] = product.id
                                stock_move_to_create["description_picking"] = product.name
                                stock_move_to_create["product_uom_qty"] = float(stock_move.get("quantity")) if float(stock_move.get("quantity")) > 0 else 1
                                #  stock_move_to_create["lot_ids"]
                                
                                if (stock_move_line_details.get("picking_type_id") and stock_move_line_type.default_location_src_id) or stock_move_line.picking_type_id.default_location_src_id:
                                    stock_move_to_create["location_id"] = stock_move_line_type.default_location_src_id.id if stock_move_line_type.default_location_src_id else stock_move_line.picking_type_id.default_location_src_id.id
                                elif (stock_move_line_details.get("partner_id") and partner.property_stock_supplier) or stock_move_line.partner_id.property_stock_supplier:
                                    stock_move_to_create["location_id"] = partner.property_stock_supplier.id if partner.property_stock_supplier else stock_move_line.partner_id.property_stock_supplier.id
                                else:
                                    stock_move_to_create["location_id"] = self.env['stock.warehouse']._get_partner_locations()

                                if (stock_move_line_details.get("picking_type_id") and stock_move_line_type.default_location_dest_id) or stock_move_line.picking_type_id.default_location_dest_id:
                                    stock_move_to_create["location_dest_id"] = stock_move_line_type.default_location_dest_id.id if stock_move_line_type.default_location_dest_id else stock_move_line.picking_type_id.default_location_dest_id.id
                                elif (stock_move_line_details.get("partner_id") and partner.property_stock_customer) or stock_move_line.partner_id.property_stock_customer:
                                    stock_move_to_create["location_dest_id"] = partner.property_stock_customer.id if partner.property_stock_customer else stock_move_line.partner_id.property_stock_customer.id
                                else:
                                    stock_move_to_create["location_dest_id"] = self.env['stock.warehouse']._get_partner_locations()
                                
                                if stock_move_to_create:
                                    stock_moves_list.append((0, 0, stock_move_to_create))
                            elif product and stock_move_id:
                                # If the product exists and the stock_move_id is present, we will update the stock_move                                
                                stock_move_to_update["name"] = product.name
                                stock_move_to_update["product_id"] = product.id
                                stock_move_to_update["description_picking"] = product.name
                                #  stock_move_to_update["lot_ids"]
                                
                                if (stock_move_line_details.get("picking_type_id") and stock_move_line_type.default_location_src_id) or stock_move_line.picking_type_id.default_location_src_id:
                                    stock_move_to_update["location_id"] = stock_move_line_type.default_location_src_id.id if stock_move_line_type.default_location_src_id else stock_move_line.picking_type_id.default_location_src_id.id
                                elif (stock_move_line_details.get("partner_id") and partner.property_stock_supplier) or stock_move_line.partner_id.property_stock_supplier:
                                    stock_move_to_update["location_id"] = partner.property_stock_supplier.id if partner.property_stock_supplier else stock_move_line.partner_id.property_stock_supplier.id
                                else:
                                    stock_move_to_update["location_id"] = self.env['stock.warehouse']._get_partner_locations()

                                if (stock_move_line_details.get("picking_type_id") and stock_move_line_type.default_location_dest_id) or stock_move_line.picking_type_id.default_location_dest_id:
                                    stock_move_to_update["location_dest_id"] = stock_move_line_type.default_location_dest_id.id if stock_move_line_type.default_location_dest_id else stock_move_line.picking_type_id.default_location_dest_id.id
                                elif (stock_move_line_details.get("partner_id") and partner.property_stock_customer) or stock_move_line.partner_id.property_stock_customer:
                                    stock_move_to_update["location_dest_id"] = partner.property_stock_customer.id if partner.property_stock_customer else stock_move_line.partner_id.property_stock_customer.id
                                else:
                                    stock_move_to_update["location_dest_id"] = self.env['stock.warehouse']._get_partner_locations()
                        
                        if stock_move.get("quantity"):
                            stock_move_to_update["product_uom_qty"] = float(stock_move.get("quantity")) if float(stock_move.get("quantity")) > 0 else 1
                        
                        # Check if there are any line stock_moves to be deleted/removed
                        if stock_move.get("delete_record") == True:
                            stock_moves_list.append((2, int(stock_move_id)))
                        
                        # Check if there are any line stock_moves to be updated
                        if stock_move.get("delete_record") == False and stock_move_to_update:
                            stock_moves_list.append((1, int(stock_move_id), stock_move_to_update))                               
                        
                    if stock_moves_list:
                        stock_move_line_details["move_ids_without_package"] = stock_moves_list
                    
                # Update stock move line details
                if stock_move_line_details:
                    stock_move_line.write(stock_move_line_details)
                    response_data["code"] = 200
                    response_data["message"] = "Updated successfully"
                else:
                    response_data["code"] = 204
                    response_data["message"] = "Nothing to update"
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock move line not found!"                    
            
            return response_data
        except TypeError as e:
            logger.error(f"Datatype error ocurred while modifying the stock move line details:\n\n{str(e)}")
            raise e
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while modifying the stock move line details:\n\n{str(e)}")
            raise e
        
    def get_the_stock_move_line(self, stock_move_line_id):
        """Get the stock move line details
        """        
        
        try:
            data = dict()
            response_data = dict()
            logged_in_user = self.env.user
            
            stock_move_line = self.env['stock.move.line'].search(
                [
                    ("id", "=", int(stock_move_line_id)),
                    ("company_id", "=", logged_in_user.company_id.id)
                ]
            )
            
            if stock_move_line:
                data["id"] = stock_move_line.id
                data["quantity"] = stock_move_line.quantity
                data["is_locked"] = stock_move_line.is_locked
                data["product"] = {"id": stock_move_line.product_id.id, "name": stock_move_line.product_id.name} if stock_move_line.product_id else {}
                data["uom"] = {"id": stock_move_line.product_uom_id.id, "name": stock_move_line.product_uom_id.name} if stock_move_line.product_uom_id else {}
                data["lot"] = {"id": stock_move_line.lot_id.id, "name": stock_move_line.lot_id.name} if stock_move_line.lot_id else {}
                data["source_stock_location"] = {"id": stock_move_line.location_id.id, "name": stock_move_line.location_id.name} if stock_move_line.location_id else {}
                data["destination_stock_location"] = {"id": stock_move_line.location_dest_id.id, "name": stock_move_line.location_dest_id.name} if stock_move_line.location_dest_id else {}
                data["stock_picking"] = {"id": stock_move_line.picking_id.id, "name": stock_move_line.picking_id.name} if stock_move_line.picking_id else {}
                data["stock_move"] = {"id": stock_move_line.move_id.id, "name": stock_move_line.move_id.name} if stock_move_line.move_id else {}
                data["stock_quantity"] = {
                    "id": stock_move_line.quant_id.id,
                    "quantity": stock_move_line.quant_id.quantity, 
                    "reserved_quantity": stock_move_line.quant_id.reserved_quantity, 
                    "available_quantity": stock_move_line.quant_id.available_quantity
                } if stock_move_line.quant_id else {}
                                    
                response_data["code"] = 200
                response_data["message"] = "Success"
                response_data["data"] = data
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock move line not found!"
            
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the stock move line details:\n\n{str(e)}")
            raise e
        
    def get_all_the_stock_move_lines(self, query_params):
        """Get all the stock move lines 
        """        
        
        try:
            response_data = dict()
            all_stock_move_lines = []
            logged_in_user = self.env.user
            search_criteria = [("company_id", "=", logged_in_user.company_id.id)]            
            
            if query_params.get("stock_picking_id"):
                stock_picking_id = query_params.get("stock_picking_id")
                search_criteria.append(
                    ("picking_id", "=", stock_picking_id)
                )
                
            if query_params.get("stock_move_id"):
                stock_move_id = query_params.get("stock_move_id")
                search_criteria.append(
                    ("move_id", "=", stock_move_id)
                )
                
            stock_move_lines = self.env['stock.move.line'].search(search_criteria)
            
            if stock_move_lines:
                for stock_move_line in stock_move_lines:
                    data = dict()
                    data["id"] = stock_move_line.id
                    data["quantity"] = stock_move_line.quantity
                    data["is_locked"] = stock_move_line.is_locked
                    data["product"] = {"id": stock_move_line.product_id.id, "name": stock_move_line.product_id.name} if stock_move_line.product_id else {}
                    data["uom"] = {"id": stock_move_line.product_uom_id.id, "name": stock_move_line.product_uom_id.name} if stock_move_line.product_uom_id else {}
                    data["lot"] = {"id": stock_move_line.lot_id.id, "name": stock_move_line.lot_id.name} if stock_move_line.lot_id else {}
                    data["source_stock_location"] = {"id": stock_move_line.location_id.id, "name": stock_move_line.location_id.name} if stock_move_line.location_id else {}
                    data["destination_stock_location"] = {"id": stock_move_line.location_dest_id.id, "name": stock_move_line.location_dest_id.name} if stock_move_line.location_dest_id else {}
                    data["stock_picking"] = {"id": stock_move_line.picking_id.id, "name": stock_move_line.picking_id.name} if stock_move_line.picking_id else {}
                    data["stock_move"] = {"id": stock_move_line.move_id.id, "name": stock_move_line.move_id.name} if stock_move_line.move_id else {}
                    data["stock_quantity"] = {
                        "id": stock_move_line.quant_id.id,
                        "quantity": stock_move_line.quant_id.quantity, 
                        "reserved_quantity": stock_move_line.quant_id.reserved_quantity, 
                        "available_quantity": stock_move_line.quant_id.available_quantity
                    } if stock_move_line.quant_id else {}
                    
                    all_stock_move_lines.append(data)
                
                response_data["code"] = 200
                response_data["message"] = "Success"
                response_data["data"] = all_stock_move_lines
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock move line not found!"
            
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the stock move lines:\n\n{str(e)}")
            raise e