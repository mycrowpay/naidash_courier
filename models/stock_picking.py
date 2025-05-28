import logging
import requests
import pytz

from datetime import datetime, date, timedelta
from odoo import models, _, fields, api
from odoo.http import request, SessionExpiredException
from odoo.exceptions import ValidationError, UserError

logger = logging.getLogger(__name__)

class NaidashStockPicking(models.Model):
    _inherit = "stock.picking"
    
    def create_the_stock_picking(self, request_data):
        """Create the stock picking
        """ 
        
        try:
            vals = dict()
            data = dict()
            response_data = dict(code=204,message="Failed to create the stock picking")
            items_to_receive = []
            logged_in_user = self.env.user            
                                    
            partner_id = request_data.get("partner_id")
            stock_picking_type_id = request_data.get("stock_picking_type_id")
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

            if not stock_picking_type_id:
                response_data["code"] = 400
                response_data["message"] = "Bad Request! Expected the stock picking type id"
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
            stock_picking_type = self.env['stock.picking.type'].search(
                [
                    ("id", "=", int(stock_picking_type_id)),
                    ("company_id", "=", logged_in_user.company_id.id)
                ]
            )
            
            if partner:
                vals["partner_id"] = partner.id
            else:
                response_data["code"] = 404
                response_data["message"] = "Partner not found!"
                return response_data                
            
            if stock_picking_type:
                vals["picking_type_id"] = stock_picking_type.id               
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
                        stock_move["name"] = product.name
                        stock_move["product_id"] = product.id
                        stock_move["description_picking"] = product.name
                        stock_move["product_uom_qty"] = float(item.get("quantity")) if float(item.get("quantity")) > 0 else 1
                        #  stock_move["lot_ids"]
                        
                        if stock_picking_type.default_location_src_id:
                            stock_move["location_id"] = stock_picking_type.default_location_src_id.id
                        elif partner.property_stock_supplier:
                            stock_move["location_id"] = partner.property_stock_supplier.id
                        else:
                            stock_move["location_id"] = self.env['stock.warehouse']._get_partner_locations()

                        if stock_picking_type.default_location_dest_id:
                            stock_move["location_dest_id"] = stock_picking_type.default_location_dest_id.id
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
            
                stock_picking = self.env['stock.picking'].create(vals)
                
                if stock_picking:
                    data['id'] = stock_picking.id
                    response_data["code"] = 201
                    response_data["message"] = "Created successfully"
                    response_data["data"] = data
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while creating the stock picking details:\n\n{str(e)}")
            raise e
        
    def edit_the_stock_picking(self, stock_picking_id, request_data):
        """Edit the stock picking details
        """ 
                
        try:
            response_data = dict()
            stock_moves_list = []
            logged_in_user = self.env.user
            stock_moves = request_data.get("stock_moves")
            stock_picking_type = self.env['stock.picking.type']
            partner = self.env['res.partner']
            
            stock_picking = self.env['stock.picking'].search(
                [
                    ("id", "=", int(stock_picking_id)),
                    ("company_id", "=", logged_in_user.company_id.id)
                ]
            )
            
            if stock_picking:
                stock_picking_details = dict()
                
                if request_data.get("date_scheduled"):
                    stock_picking_details["scheduled_date"] = request_data.get("date_scheduled")

                if request_data.get("origin"):
                    stock_picking_details["origin"] = request_data.get("origin")
                    
                if request_data.get("notes"):
                    stock_picking_details["note"] = request_data.get("notes")
                                    
                if request_data.get("assigned_user_id"):
                    assigned_user_id = request_data.get("assigned_user_id")
                    user = self.env['res.users'].search(
                        [
                            ('id', '=', int(assigned_user_id)),
                            ('company_id', '=', logged_in_user.company_id.id)
                        ]
                    )
                    
                    if user:
                        stock_picking_details["user_id"] = user.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "User not found!"
                        return response_data
                
                if request_data.get("partner_id"):
                    partner_id = request_data.get("partner_id")
                    partner = partner.browse(int(partner_id))
                    
                    if partner:
                        stock_picking_details["partner_id"] = partner.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Partner not found!"
                        return response_data
                    
                if request_data.get("stock_picking_type_id"):
                    stock_picking_type_id = request_data.get("stock_picking_type_id")                    
                    stock_picking_type = stock_picking_type.search(
                        [
                            ("id", "=", int(stock_picking_type_id)),
                            ("company_id", "=", logged_in_user.company_id.id)
                        ]
                    )
                                        
                    if stock_picking_type:
                        stock_picking_details["picking_type_id"] = stock_picking_type.id
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
                                
                                if (stock_picking_details.get("picking_type_id") and stock_picking_type.default_location_src_id) or stock_picking.picking_type_id.default_location_src_id:
                                    stock_move_to_create["location_id"] = stock_picking_type.default_location_src_id.id if stock_picking_type.default_location_src_id else stock_picking.picking_type_id.default_location_src_id.id
                                elif (stock_picking_details.get("partner_id") and partner.property_stock_supplier) or stock_picking.partner_id.property_stock_supplier:
                                    stock_move_to_create["location_id"] = partner.property_stock_supplier.id if partner.property_stock_supplier else stock_picking.partner_id.property_stock_supplier.id
                                else:
                                    stock_move_to_create["location_id"] = self.env['stock.warehouse']._get_partner_locations()

                                if (stock_picking_details.get("picking_type_id") and stock_picking_type.default_location_dest_id) or stock_picking.picking_type_id.default_location_dest_id:
                                    stock_move_to_create["location_dest_id"] = stock_picking_type.default_location_dest_id.id if stock_picking_type.default_location_dest_id else stock_picking.picking_type_id.default_location_dest_id.id
                                elif (stock_picking_details.get("partner_id") and partner.property_stock_customer) or stock_picking.partner_id.property_stock_customer:
                                    stock_move_to_create["location_dest_id"] = partner.property_stock_customer.id if partner.property_stock_customer else stock_picking.partner_id.property_stock_customer.id
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
                                
                                if (stock_picking_details.get("picking_type_id") and stock_picking_type.default_location_src_id) or stock_picking.picking_type_id.default_location_src_id:
                                    stock_move_to_update["location_id"] = stock_picking_type.default_location_src_id.id if stock_picking_type.default_location_src_id else stock_picking.picking_type_id.default_location_src_id.id
                                elif (stock_picking_details.get("partner_id") and partner.property_stock_supplier) or stock_picking.partner_id.property_stock_supplier:
                                    stock_move_to_update["location_id"] = partner.property_stock_supplier.id if partner.property_stock_supplier else stock_picking.partner_id.property_stock_supplier.id
                                else:
                                    stock_move_to_update["location_id"] = self.env['stock.warehouse']._get_partner_locations()

                                if (stock_picking_details.get("picking_type_id") and stock_picking_type.default_location_dest_id) or stock_picking.picking_type_id.default_location_dest_id:
                                    stock_move_to_update["location_dest_id"] = stock_picking_type.default_location_dest_id.id if stock_picking_type.default_location_dest_id else stock_picking.picking_type_id.default_location_dest_id.id
                                elif (stock_picking_details.get("partner_id") and partner.property_stock_customer) or stock_picking.partner_id.property_stock_customer:
                                    stock_move_to_update["location_dest_id"] = partner.property_stock_customer.id if partner.property_stock_customer else stock_picking.partner_id.property_stock_customer.id
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
                        stock_picking_details["move_ids_without_package"] = stock_moves_list
                    
                # Update stock picking details
                if stock_picking_details:
                    stock_picking.write(stock_picking_details)
                    response_data["code"] = 200
                    response_data["message"] = "Updated successfully"
                else:
                    response_data["code"] = 204
                    response_data["message"] = "Nothing to update"
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock picking not found!"                    
            
            return response_data
        except TypeError as e:
            logger.error(f"Datatype error ocurred while modifying the stock picking details:\n\n{str(e)}")
            raise e
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while modifying the stock picking details:\n\n{str(e)}")
            raise e
        
    def get_the_stock_picking(self, stock_picking_id):
        """Get the stock picking details
        """        
        
        try:
            data = dict()
            response_data = dict()
            logged_in_user = self.env.user
            
            stock_picking = self.env['stock.picking'].search(
                [
                    ("id", "=", int(stock_picking_id)),
                    ("company_id", "=", logged_in_user.company_id.id)
                ]
            )
            
            if stock_picking:
                data["id"] = stock_picking.id
                data["name"] = stock_picking.name or ""
                data["status"] = {"id": stock_picking.state, "name": dict(stock_picking._fields['state'].selection).get(stock_picking.state, stock_picking.state)}
                data["origin"] = stock_picking.origin or ""
                data["notes"] = stock_picking.note or ""
                data["date_scheduled"] = ""
                data["date_processed"] = ""
                
                # Display the scheduled time using the logged in user's timezone
                if stock_picking.scheduled_date:
                    user_timezone = logged_in_user.tz or pytz.utc
                    user_timezone = pytz.timezone(user_timezone)
                    scheduled_date = (stock_picking.scheduled_date).strftime("%Y-%m-%d %H:%M")
                    scheduled_date = datetime.strftime(
                        pytz.utc.localize(datetime.strptime(scheduled_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                        "%Y-%m-%d %H:%M"
                    )
                    
                    data["date_scheduled"] = scheduled_date
                    
                # Display the processed time using the logged in user's timezone
                if stock_picking.date_done:
                    user_timezone = logged_in_user.tz or pytz.utc
                    user_timezone = pytz.timezone(user_timezone)
                    date_done = (stock_picking.date_done).strftime("%Y-%m-%d %H:%M")
                    date_done = datetime.strftime(
                        pytz.utc.localize(datetime.strptime(date_done, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                        "%Y-%m-%d %H:%M"
                    )
                    
                    data["date_processed"] = date_done
                
                data["stock_picking_type_code"] = stock_picking.picking_type_code or ""
                data["partner"] = {"id": stock_picking.partner_id.id, "name": stock_picking.partner_id.name} if stock_picking.partner_id else {}
                data["stock_picking_type"] = {"id": stock_picking.picking_type_id.id, "name": stock_picking.picking_type_id.name} if stock_picking.picking_type_id else {}
                data["company"] = {"id": stock_picking.company_id.id, "name": stock_picking.company_id.name} if stock_picking.company_id else {}
                data["stock_lot"] = {"id": stock_picking.lot_id.id, "name": stock_picking.lot_id.name} if stock_picking.lot_id else {}
                data["assigned_user"] = {"id": stock_picking.user_id.id, "name": stock_picking.user_id.name} if stock_picking.user_id else {}
                data["stock_moves"] = [
                    {
                        "id": stock_move.id,
                        "description": stock_move.description_picking or "",
                        "quantity": stock_move.product_uom_qty,
                        "product": {"id": stock_move.product_id.id, "name": stock_move.product_id.name} if stock_move.product_id else {},
                        "stock_move_lines": [
                            {
                                "id": stock_move_line.id, 
                                "quantity": stock_move_line.quantity,
                                "lot_provisional_name": stock_move_line.lot_name or "",
                                "product": {"id": stock_move_line.product_id.id, "name": stock_move_line.product_id.name} if stock_move_line.product_id else {},
                                "uom": {"id": stock_move_line.product_uom_id.id, "name": stock_move_line.product_uom_id.name} if stock_move_line.product_uom_id else {},
                                "lot": {"id": stock_move_line.lot_id.id, "name": stock_move_line.lot_id.name} if stock_move_line.lot_id else {},
                                "destination_stock_location": {"id": stock_move_line.location_dest_id.id, "name": stock_move_line.location_dest_id.name} if stock_move_line.location_dest_id else {}
                            } for stock_move_line in stock_move.move_line_ids
                        ] if stock_move.move_line_ids else [] # stock_move.move_line_ids_without_package
                        
                    } for stock_move in stock_picking.move_ids_without_package
                ] if stock_picking.move_ids_without_package else []
                                    
                response_data["code"] = 200
                response_data["message"] = "Success"
                response_data["data"] = data
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock picking not found!"
            
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the stock picking details:\n\n{str(e)}")
            raise e
        
    def get_all_the_stock_pickings(self, query_params):
        """Get all the stock pickings 
        """        
        
        try:
            response_data = dict()
            all_stock_pickings = []
            logged_in_user = self.env.user
            search_criteria = [("company_id", "=", logged_in_user.company_id.id)]
            
            
            if query_params.get("stock_picking_type_code"):
                stock_picking_type_code = query_params.get("stock_picking_type_code")
                search_criteria.append(
                    ("picking_type_code", "=", stock_picking_type_code)
                )
                
            if query_params.get("date_scheduled"):
                scheduled_date = query_params.get("date_scheduled")
                search_criteria.append(
                    ('scheduled_date', '>=', f"{scheduled_date} 00:00:00")
                )
                search_criteria.append(
                    ('scheduled_date', '<=', f"{scheduled_date} 23:59:59")
                )
                
            if query_params.get("status"):
                status = query_params.get("status")
                search_criteria.append(
                    ('state','=', status)
                )         

            stock_pickings = self.env['stock.picking'].search(search_criteria)
            
            if stock_pickings:
                for stock_picking in stock_pickings:
                    data = dict()
                    data["id"] = stock_picking.id
                    data["name"] = stock_picking.name or ""
                    data["status"] = {"id": stock_picking.state, "name": dict(stock_picking._fields['state'].selection).get(stock_picking.state, stock_picking.state)}
                    data["origin"] = stock_picking.origin or ""
                    data["notes"] = stock_picking.note or ""
                    data["date_scheduled"] = ""
                    data["date_processed"] = ""
                    
                    # Display the scheduled time using the logged in user's timezone
                    if stock_picking.scheduled_date:
                        user_timezone = logged_in_user.tz or pytz.utc
                        user_timezone = pytz.timezone(user_timezone)
                        scheduled_date = (stock_picking.scheduled_date).strftime("%Y-%m-%d %H:%M")
                        scheduled_date = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(scheduled_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["date_scheduled"] = scheduled_date
                        
                    # Display the processed time using the logged in user's timezone
                    if stock_picking.date_done:
                        user_timezone = logged_in_user.tz or pytz.utc
                        user_timezone = pytz.timezone(user_timezone)
                        date_done = (stock_picking.date_done).strftime("%Y-%m-%d %H:%M")
                        date_done = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(date_done, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["date_processed"] = date_done
                        
                    data["stock_picking_type_code"] = stock_picking.picking_type_code or ""
                    data["partner"] = {"id": stock_picking.partner_id.id, "name": stock_picking.partner_id.name} if stock_picking.partner_id else {}
                    data["stock_picking_type"] = {"id": stock_picking.picking_type_id.id, "name": stock_picking.picking_type_id.name} if stock_picking.picking_type_id else {}
                    data["company"] = {"id": stock_picking.company_id.id, "name": stock_picking.company_id.name} if stock_picking.company_id else {}
                    data["assigned_user"] = {"id": stock_picking.user_id.id, "name": stock_picking.user_id.name} if stock_picking.user_id else {}                
                    data["stock_moves"] = [
                        {
                            "id": stock_move.id,
                            "description": stock_move.description_picking or "",
                            "quantity": stock_move.product_uom_qty,
                            "product": {"id": stock_move.product_id.id, "name": stock_move.product_id.name} if stock_move.product_id else {},
                            "stock_move_lines": [
                                {
                                    "id": stock_move_line.id, 
                                    "quantity": stock_move_line.quantity,
                                    "lot_provisional_name": stock_move_line.lot_name or "",
                                    "product": {"id": stock_move_line.product_id.id, "name": stock_move_line.product_id.name} if stock_move_line.product_id else {},
                                    "uom": {"id": stock_move_line.product_uom_id.id, "name": stock_move_line.product_uom_id.name} if stock_move_line.product_uom_id else {},
                                    "lot": {"id": stock_move_line.lot_id.id, "name": stock_move_line.lot_id.name} if stock_move_line.lot_id else {},
                                    "destination_stock_location": {"id": stock_move_line.location_dest_id.id, "name": stock_move_line.location_dest_id.name} if stock_move_line.location_dest_id else {}
                                } for stock_move_line in stock_move.move_line_ids
                            ] if stock_move.move_line_ids else [] # stock_move.move_line_ids_without_package
                            
                        } for stock_move in stock_picking.move_ids_without_package
                    ] if stock_picking.move_ids_without_package else []
                    
                    all_stock_pickings.append(data)
                
                response_data["code"] = 200
                response_data["message"] = "Success"
                response_data["data"] = all_stock_pickings
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock picking not found!"
            
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the stock pickings:\n\n{str(e)}")
            raise e
        
    def confirm_the_stock_picking_details(self, stock_picking_id):
        """Confirm the stock picking details
        """        
        
        try:
            response_data = dict()            
            stock_picking = self.env['stock.picking'].browse(int(stock_picking_id))
            
            if stock_picking:
                if stock_picking.state != "draft":
                    response_data["code"] = 400
                    response_data["message"] = f"Bad Request! '{stock_picking.name}' cannot be confirmed while in the '{dict(stock_picking._fields['state'].selection).get(stock_picking.state, stock_picking.state)}' state"                    
                    return response_data
                
                confirm = stock_picking.action_confirm()
                
                response_data["code"] = 200
                response_data["message"] = "Stock picking confirmed"
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock picking not found!"
            
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"The following error ocurred while confirming the stock picking details:\n\n{str(e)}")
            raise e
        
    def validate_the_stock_picking_details(self, stock_picking_id):
        """Validate the stock picking details
        """        
        
        try:
            response_data = dict()            
            stock_picking = self.env['stock.picking'].browse(int(stock_picking_id))
            
            if stock_picking:
                if (stock_picking.picking_type_code == "incoming" and stock_picking.state in ["waiting", "assigned", "done", "cancel"]) or \
                    (stock_picking.picking_type_code == "outgoing" and stock_picking.state in ["draft", "confirmed", "done", "cancel"]):
                        response_data["code"] = 400
                        response_data["message"] = f"Bad Request! '{stock_picking.name}' cannot be validated while in the '{dict(stock_picking._fields['state'].selection).get(stock_picking.state, stock_picking.state)}' state"
                        return response_data
                
                validate = stock_picking.button_validate()
                
                response_data["code"] = 200
                response_data["message"] = "Stock picking validated"
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock picking not found!"
            
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"The following error ocurred while validating the stock picking details:\n\n{str(e)}")
            raise e
        
    def cancel_the_stock_picking_details(self, stock_picking_id):
        """Cancel the stock picking details
        """        
        
        try:
            response_data = dict()            
            stock_picking = self.env['stock.picking'].browse(int(stock_picking_id))
            
            if stock_picking:
                if stock_picking.state not in ["assigned", "confirmed", "draft", "waiting"]:
                    response_data["code"] = 400
                    response_data["message"] = f"Bad Request! '{stock_picking.name}' cannot be cancelled while in the '{dict(stock_picking._fields['state'].selection).get(stock_picking.state, stock_picking.state)}' state"
                    return response_data
                
                cancel = stock_picking.action_cancel()
                
                response_data["code"] = 200
                response_data["message"] = "Stock picking cancelled"
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock picking not found!"
            
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"The following error ocurred while cancelling the stock picking details:\n\n{str(e)}")
            raise e