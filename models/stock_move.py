import logging
import requests
import pytz

from collections import defaultdict
from datetime import datetime, date, timedelta
from odoo import models, _, fields, api
from odoo.http import request, SessionExpiredException
from odoo.exceptions import ValidationError, UserError

logger = logging.getLogger(__name__)

class NaidashStockMove(models.Model):
    _inherit = "stock.move"
    
    def create_the_stock_move(self, request_data):
        """Create the stock move
        """ 
        
        try:
            vals = dict()
            data = dict()
            response_data = dict(code=204,message="Failed to create the stock move")
            items_to_receive = []
            logged_in_user = self.env.user            
                                    
            partner_id = request_data.get("partner_id")
            stock_move_type_id = request_data.get("stock_move_type_id")
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

            if not stock_move_type_id:
                response_data["code"] = 400
                response_data["message"] = "Bad Request! Expected the stock move type id"
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
            stock_move_type = self.env['stock.move.type'].search(
                [
                    ("id", "=", int(stock_move_type_id)),
                    ("company_id", "=", logged_in_user.company_id.id)
                ]
            )
            
            if partner:
                vals["partner_id"] = partner.id
            else:
                response_data["code"] = 404
                response_data["message"] = "Partner not found!"
                return response_data                
            
            if stock_move_type:
                vals["picking_type_id"] = stock_move_type.id               
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
                        
                        if stock_move_type.default_location_src_id:
                            stock_move["location_id"] = stock_move_type.default_location_src_id.id
                        elif partner.property_stock_supplier:
                            stock_move["location_id"] = partner.property_stock_supplier.id
                        else:
                            stock_move["location_id"] = self.env['stock.warehouse']._get_partner_locations()

                        if stock_move_type.default_location_dest_id:
                            stock_move["location_dest_id"] = stock_move_type.default_location_dest_id.id
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
            
                stock_move = self.env['stock.move'].create(vals)
                
                if stock_move:
                    data['id'] = stock_move.id
                    response_data["code"] = 201
                    response_data["message"] = "Created successfully"
                    response_data["data"] = data
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while creating the stock move details:\n\n{str(e)}")
            raise e
        
    def edit_the_stock_move(self, stock_move_id, request_data):
        """Edit the stock move details
        """ 
                
        try:
            response_data = dict()
            stock_moves_list = []
            logged_in_user = self.env.user
            stock_moves = request_data.get("stock_moves")
            stock_move_type = self.env['stock.move.type']
            partner = self.env['res.partner']
            
            stock_move = self.env['stock.move'].search(
                [
                    ("id", "=", int(stock_move_id)),
                    ("company_id", "=", logged_in_user.company_id.id)
                ]
            )
            
            if stock_move:
                stock_move_details = dict()
                
                if request_data.get("date_scheduled"):
                    stock_move_details["scheduled_date"] = request_data.get("date_scheduled")

                if request_data.get("origin"):
                    stock_move_details["origin"] = request_data.get("origin")
                    
                if request_data.get("notes"):
                    stock_move_details["note"] = request_data.get("notes")
                                    
                if request_data.get("assigned_user_id"):
                    assigned_user_id = request_data.get("assigned_user_id")
                    user = self.env['res.users'].search(
                        [
                            ('id', '=', int(assigned_user_id)),
                            ('company_id', '=', logged_in_user.company_id.id)
                        ]
                    )
                    
                    if user:
                        stock_move_details["user_id"] = user.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "User not found!"
                        return response_data
                
                if request_data.get("partner_id"):
                    partner_id = request_data.get("partner_id")
                    partner = partner.browse(int(partner_id))
                    
                    if partner:
                        stock_move_details["partner_id"] = partner.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Partner not found!"
                        return response_data
                    
                if request_data.get("stock_move_type_id"):
                    stock_move_type_id = request_data.get("stock_move_type_id")                    
                    stock_move_type = stock_move_type.search(
                        [
                            ("id", "=", int(stock_move_type_id)),
                            ("company_id", "=", logged_in_user.company_id.id)
                        ]
                    )
                                        
                    if stock_move_type:
                        stock_move_details["picking_type_id"] = stock_move_type.id
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
                                
                                if (stock_move_details.get("picking_type_id") and stock_move_type.default_location_src_id) or stock_move.picking_type_id.default_location_src_id:
                                    stock_move_to_create["location_id"] = stock_move_type.default_location_src_id.id if stock_move_type.default_location_src_id else stock_move.picking_type_id.default_location_src_id.id
                                elif (stock_move_details.get("partner_id") and partner.property_stock_supplier) or stock_move.partner_id.property_stock_supplier:
                                    stock_move_to_create["location_id"] = partner.property_stock_supplier.id if partner.property_stock_supplier else stock_move.partner_id.property_stock_supplier.id
                                else:
                                    stock_move_to_create["location_id"] = self.env['stock.warehouse']._get_partner_locations()

                                if (stock_move_details.get("picking_type_id") and stock_move_type.default_location_dest_id) or stock_move.picking_type_id.default_location_dest_id:
                                    stock_move_to_create["location_dest_id"] = stock_move_type.default_location_dest_id.id if stock_move_type.default_location_dest_id else stock_move.picking_type_id.default_location_dest_id.id
                                elif (stock_move_details.get("partner_id") and partner.property_stock_customer) or stock_move.partner_id.property_stock_customer:
                                    stock_move_to_create["location_dest_id"] = partner.property_stock_customer.id if partner.property_stock_customer else stock_move.partner_id.property_stock_customer.id
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
                                
                                if (stock_move_details.get("picking_type_id") and stock_move_type.default_location_src_id) or stock_move.picking_type_id.default_location_src_id:
                                    stock_move_to_update["location_id"] = stock_move_type.default_location_src_id.id if stock_move_type.default_location_src_id else stock_move.picking_type_id.default_location_src_id.id
                                elif (stock_move_details.get("partner_id") and partner.property_stock_supplier) or stock_move.partner_id.property_stock_supplier:
                                    stock_move_to_update["location_id"] = partner.property_stock_supplier.id if partner.property_stock_supplier else stock_move.partner_id.property_stock_supplier.id
                                else:
                                    stock_move_to_update["location_id"] = self.env['stock.warehouse']._get_partner_locations()

                                if (stock_move_details.get("picking_type_id") and stock_move_type.default_location_dest_id) or stock_move.picking_type_id.default_location_dest_id:
                                    stock_move_to_update["location_dest_id"] = stock_move_type.default_location_dest_id.id if stock_move_type.default_location_dest_id else stock_move.picking_type_id.default_location_dest_id.id
                                elif (stock_move_details.get("partner_id") and partner.property_stock_customer) or stock_move.partner_id.property_stock_customer:
                                    stock_move_to_update["location_dest_id"] = partner.property_stock_customer.id if partner.property_stock_customer else stock_move.partner_id.property_stock_customer.id
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
                        stock_move_details["move_ids_without_package"] = stock_moves_list
                    
                # Update stock move details
                if stock_move_details:
                    stock_move.write(stock_move_details)
                    response_data["code"] = 200
                    response_data["message"] = "Updated successfully"
                else:
                    response_data["code"] = 204
                    response_data["message"] = "Nothing to update"
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock move not found!"                    
            
            return response_data
        except TypeError as e:
            logger.error(f"Datatype error ocurred while modifying the stock move details:\n\n{str(e)}")
            raise e
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while modifying the stock move details:\n\n{str(e)}")
            raise e
        
    def get_the_stock_move(self, stock_move_id):
        """Get the stock move details
        """        
        
        try:
            data = dict()
            response_data = dict()
            logged_in_user = self.env.user
            
            stock_move = self.env['stock.move'].search(
                [
                    ("id", "=", int(stock_move_id)),
                    ("company_id", "=", logged_in_user.company_id.id)
                ]
            )
            
            if stock_move:
                data["id"] = stock_move.id
                data["description"] = stock_move.description_picking or ""
                data["quantity"] = stock_move.product_uom_qty
                data["stock_move_line_quantity"] = stock_move.quantity
                data["is_picked"] = stock_move.picked
                data["is_locked"] = stock_move.is_locked
                data["schedule_date"] = ""
                data["due_date"] = ""
                data["origin"] = stock_move.origin or ""
                
                # Display the scheduled date using the logged in user's timezone
                if stock_move.date:
                    user_timezone = logged_in_user.tz or pytz.utc
                    user_timezone = pytz.timezone(user_timezone)
                    scheduled_date = (stock_move.date).strftime("%Y-%m-%d %H:%M")
                    scheduled_date = datetime.strftime(
                        pytz.utc.localize(datetime.strptime(scheduled_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                        "%Y-%m-%d %H:%M"
                    )
                    
                    data["schedule_date"] = scheduled_date
                    
                # Display the due date using the logged in user's timezone
                if stock_move.date_deadline:
                    user_timezone = logged_in_user.tz or pytz.utc
                    user_timezone = pytz.timezone(user_timezone)
                    date_done = (stock_move.date_deadline).strftime("%Y-%m-%d %H:%M")
                    date_done = datetime.strftime(
                        pytz.utc.localize(datetime.strptime(date_done, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                        "%Y-%m-%d %H:%M"
                    )
                    
                    data["due_date"] = date_done
                    
                data["status"] = {"id": stock_move.state, "name": dict(stock_move._fields['state'].selection).get(stock_move.state, stock_move.state)}
                data["stock_picking"] = {"id": stock_move.picking_id.id, "name": stock_move.picking_id.name} if stock_move.picking_id else {}
                data["product"] = {"id": stock_move.product_id.id, "name": stock_move.product_id.name} if stock_move.product_id else {}
                data["uom"] = {"id": stock_move.product_uom.id, "name": stock_move.product_uom.name} if stock_move.product_uom else {}
                data["source_stock_location"] = {"id": stock_move.location_id.id, "name": stock_move.location_id.name} if stock_move.location_id else {}
                data["destination_stock_location"] = {"id": stock_move.location_dest_id.id, "name": stock_move.location_dest_id.name} if stock_move.location_dest_id else {}
                data["stock_lots"] = [
                    {
                        "id": lot.id, 
                        "name": lot.name
                    } for lot in stock_move.lot_ids
                ] if stock_move.lot_ids else []
                
                data["stock_move_lines"] = [
                    {
                        "id": stock_move_line.id, 
                        "quantity": stock_move_line.quantity,
                        "product": {"id": stock_move_line.product_id.id, "name": stock_move_line.product_id.name} if stock_move_line.product_id else {},
                        "uom": {"id": stock_move_line.product_uom_id.id, "name": stock_move_line.product_uom_id.name} if stock_move_line.product_uom_id else {},
                        "lot": {"id": stock_move_line.lot_id.id, "name": stock_move_line.lot_id.name} if stock_move_line.lot_id else {},
                        "source_stock_location": {"id": stock_move_line.location_id.id, "name": stock_move_line.location_id.name} if stock_move_line.location_id else {},
                        "destination_stock_location": {"id": stock_move_line.location_dest_id.id, "name": stock_move_line.location_dest_id.name} if stock_move_line.location_dest_id else {}
                    } for stock_move_line in stock_move.move_line_ids
                ] if stock_move.move_line_ids else [] # stock_move.move_line_ids_without_package
                                    
                response_data["code"] = 200
                response_data["message"] = "Success"
                response_data["data"] = data
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock move not found!"
            
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the stock move details:\n\n{str(e)}")
            raise e
        
    def get_all_the_stock_moves(self, query_params):
        """Get all the stock moves 
        """        
        
        try:
            response_data = dict()
            all_stock_moves = []
            logged_in_user = self.env.user
            search_criteria = [("company_id", "=", logged_in_user.company_id.id)]
            
            if not query_params:
                response_data["code"] = 400
                response_data["message"] = "Bad request! Missing query parameters."
                return response_data
            
            if query_params.get("stock_picking_id"):
                stock_picking_id = query_params.get("stock_picking_id")
                search_criteria.append(
                    ('picking_id', '=', int(stock_picking_id))
                )

            stock_moves = self.env['stock.move'].search(search_criteria, order='id asc')
            
            if stock_moves:
                for stock_move in stock_moves:
                    data = dict()
                    data["id"] = stock_move.id
                    data["description"] = stock_move.description_picking or ""
                    data["quantity"] = stock_move.product_uom_qty
                    data["stock_move_line_quantity"] = stock_move.quantity
                    data["is_picked"] = stock_move.picked
                    data["is_locked"] = stock_move.is_locked
                    data["schedule_date"] = ""
                    data["due_date"] = ""
                    data["origin"] = stock_move.origin or ""
                    
                    # Display the scheduled date using the logged in user's timezone
                    if stock_move.date:
                        user_timezone = logged_in_user.tz or pytz.utc
                        user_timezone = pytz.timezone(user_timezone)
                        scheduled_date = (stock_move.date).strftime("%Y-%m-%d %H:%M")
                        scheduled_date = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(scheduled_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["schedule_date"] = scheduled_date
                        
                    # Display the due date using the logged in user's timezone
                    if stock_move.date_deadline:
                        user_timezone = logged_in_user.tz or pytz.utc
                        user_timezone = pytz.timezone(user_timezone)
                        date_done = (stock_move.date_deadline).strftime("%Y-%m-%d %H:%M")
                        date_done = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(date_done, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["due_date"] = date_done
                        
                    data["status"] = {"id": stock_move.state, "name": dict(stock_move._fields['state'].selection).get(stock_move.state, stock_move.state)}
                    data["stock_picking"] = {"id": stock_move.picking_id.id, "name": stock_move.picking_id.name} if stock_move.picking_id else {}
                    data["product"] = {"id": stock_move.product_id.id, "name": stock_move.product_id.name} if stock_move.product_id else {}
                    data["uom"] = {"id": stock_move.product_uom.id, "name": stock_move.product_uom.name} if stock_move.product_uom else {}
                    data["source_stock_location"] = {"id": stock_move.location_id.id, "name": stock_move.location_id.name} if stock_move.location_id else {}
                    data["destination_stock_location"] = {"id": stock_move.location_dest_id.id, "name": stock_move.location_dest_id.name} if stock_move.location_dest_id else {}
                    data["stock_lots"] = [
                        {
                            "id": lot.id, 
                            "name": lot.name
                        } for lot in stock_move.lot_ids
                    ] if stock_move.lot_ids else []
                    
                    data["stock_move_lines"] = [
                        {
                            "id": stock_move_line.id, 
                            "quantity": stock_move_line.quantity,
                            "product": {"id": stock_move_line.product_id.id, "name": stock_move_line.product_id.name} if stock_move_line.product_id else {},
                            "uom": {"id": stock_move_line.product_uom_id.id, "name": stock_move_line.product_uom_id.name} if stock_move_line.product_uom_id else {},
                            "lot": {"id": stock_move_line.lot_id.id, "name": stock_move_line.lot_id.name} if stock_move_line.lot_id else {},
                            "source_stock_location": {"id": stock_move_line.location_id.id, "name": stock_move_line.location_id.name} if stock_move_line.location_id else {},
                            "destination_stock_location": {"id": stock_move_line.location_dest_id.id, "name": stock_move_line.location_dest_id.name} if stock_move_line.location_dest_id else {}
                        } for stock_move_line in stock_move.move_line_ids
                    ] if stock_move.move_line_ids else [] # stock_move.move_line_ids_without_package
                    
                    all_stock_moves.append(data)
                
                response_data["code"] = 200
                response_data["message"] = "Success"
                response_data["data"] = all_stock_moves
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock move not found!"
            
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the stock moves:\n\n{str(e)}")
            raise e
        
        
    def assign_serial_numbers_to_stock_move(self, stock_move_id, request_data):
        """
        Assign serial numbers to each stock move quantity.
        The number of serial numbers must not exceed the stock move quantity.
        Serial numbers are provided by the user and are not auto-incremented.

        :param stock_move_id: ID of the stock move
        :param request_data: List of serial numbers to assign
        :return: dict with status and message
        """
        try:
            response_data = dict()
            logged_in_user = self.env.user
            
            if not request_data:
                response_data["code"] = 400
                response_data["message"] = "Bad request! Empty JSON body received."
                return response_data
                        
            serial_numbers = request_data.get("serial_numbers")

            if not isinstance(serial_numbers, list) or not serial_numbers:
                response_data["code"] = 400
                response_data["message"] = "Serial numbers must be a non-empty list."
                return response_data
            
            stock_move = self.env['stock.move'].search(
                [
                    ("id", "=", int(stock_move_id)),
                    ("company_id", "=", logged_in_user.company_id.id)
                ]
            )

            if stock_move:
                for serial_no in serial_numbers:
                    try:
                        serial_no = "".join(serial_no.split())
                        stock_move._generate_serial_numbers(serial_no, next_serial_count=1)
                    except (ValidationError, UserError) as e:
                        logger.warning(f"Failed to assign serial number '{serial_no}': {str(e)}")
                        continue
                    
                response_data["code"] = 201
                response_data["message"] = "Serial numbers created successfully."
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock move not found!"
                
            return response_data

        except Exception as e:
            logger.error(f"Error assigning serial numbers to stock move:\n\n{str(e)}")
            raise e