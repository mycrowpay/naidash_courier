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
            response_data = dict()
            items_to_receive = []
                                    
            partner_id = request_data.get("partner_id")
            stock_picking_type_id = request_data.get("stock_picking_type_id")
            assigned_user_id = request_data.get("assigned_user_id")
            line_items = request_data.get("line_items")
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
            
            if not line_items:
                response_data["code"] = 400
                response_data["message"] = "Bad Request! Add the items to receive"
                return response_data
                            
            if isinstance(line_items, list) == False:
                response_data["code"] = 422
                response_data["message"] = "Unprocessable Content! Expected a list of objects in `line_items`"
                return response_data
            
            if assigned_user_id:
                user = self.env['res.users'].browse(int(assigned_user_id))
                
                if user:
                    vals["user_id"] = user.id
                else:
                    response_data["code"] = 404
                    response_data["message"] = "User not found!"
                    return response_data                
            
            partner = self.env['res.partner'].browse(int(partner_id))
            stock_picking_type = self.env['stock.picking.type'].browse(int(stock_picking_type_id))
            
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
            
            for item in line_items:
                items = dict()
                product_id = item.get("product_id")
                # source_location_id = item.get("source_location_id")
                # destination_location_id = item.get("destination_location_id")
                
                # if source_location_id:
                #     source_location = self.env['stock.location'].browse(int(source_location_id))
                    
                #     if source_location:
                #         items["location_id"] = source_location.id
                #         items["location_dest_id"] = destination_location_id
                #     else:
                #         response_data["code"] = 404
                #         response_data["message"] = "Source location not found!"
                #         return response_data
                # else:
                
                if product_id:
                    product = self.env['product.product'].search(
                        [
                            ('id', '=', int(product_id)),
                            ('detailed_type', 'in', ['product', 'consu'])
                        ]
                    )
                    
                    if product:
                        items["product_id"] = product.id
                        items["description_picking"] = product.name
                        items["product_uom_qty"] = float(item.get("quantity")) if float(item.get("quantity")) > 0 else 1
                    
                if items:                        
                    items_to_receive.append((0, 0, items))
                    
            if items_to_receive:
                vals["move_ids_without_package"] = items_to_receive
            
                stock_picking = self.env['stock.picking'].create(vals)
                
                if stock_picking:
                    data['id'] = stock_picking.id
                    response_data["code"] = 201
                    response_data["message"] = "Created successfully"
                    response_data["data"] = data
                else:
                    response_data["code"] = 204
                    response_data["message"] = "Failed to create the stock receipt"
                    return response_data
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while creating the stock picking receipt:\n\n{str(e)}")
            raise e
        
    def edit_the_stock_picking(self, stock_picking_id, request_data):
        """Edit the stock picking details
        """ 
                
        try:
            response_data = dict()
            items_to_receive = []
            logged_in_user = self.env.user
            line_items = request_data.get("line_items")
            
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
                    user = self.env['res.users'].browse(int(assigned_user_id))
                    
                    if user:
                        stock_picking_details["user_id"] = user.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "User not found!"
                        return response_data                
                
                if request_data.get("partner_id"):
                    partner_id = request_data.get("partner_id")
                    partner = self.env['res.partner'].browse(int(partner_id))
                    
                    if partner:
                        stock_picking_details["partner_id"] = partner.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Partner not found!"
                        return response_data
                    
                if request_data.get("stock_picking_type_id"):
                    stock_picking_type_id = request_data.get("stock_picking_type_id")                    
                    stock_picking_type = self.env['stock.picking.type'].browse(int(stock_picking_type_id))                    
                    
                    if stock_picking_type:
                        stock_picking_details["picking_type_id"] = stock_picking_type.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Operation type not found!"
                        return response_data
                    
                if line_items and isinstance(line_items, list):
                    for item in line_items:
                        item_to_update = dict()
                        item_to_create = dict()
                        item_id = item.get("id")
                        product_id = item.get("product_id")
                        
                        if product_id:
                            product = self.env['product.product'].search(
                                [
                                    ('id', '=', int(product_id)),
                                    ('detailed_type', 'in', ['product', 'consu'])
                                ]
                            )
                            
                            if product and not item_id:
                                # If the product exists and the item_id is not present, we will create a new item
                                item_to_create["product_id"] = product.id
                                item_to_create["description_picking"] = product.name
                                item_to_create["product_uom_qty"] = float(item.get("quantity")) if float(item.get("quantity")) > 0 else 1                            
                                
                                if item_to_create:
                                    items_to_receive.append((0, 0, item_to_create))
                            elif product and item_id:
                                # If the product exists and the item_id is present, we will update the item                                
                                item_to_update["product_id"] = product.id
                                item_to_update["description_picking"] = product.name
                        
                        if item.get("quantity"):
                            item_to_update["product_uom_qty"] = float(item.get("quantity")) if float(item.get("quantity")) > 0 else 1
                        
                        # Check if there are any line items to be deleted/removed
                        if item.get("delete_record") == True:
                            items_to_receive.append((2, int(item_id)))
                        
                        # Check if there are any line items to be updated
                        if item.get("delete_record") == False and item_to_update:
                            items_to_receive.append((1, int(item_id), item_to_update))                               
                        
                    if items_to_receive:
                        stock_picking_details["move_ids_without_package"] = items_to_receive                    
                    
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
                data["assigned_user"] = {"id": stock_picking.user_id.id, "name": stock_picking.user_id.name} if stock_picking.user_id else {}                
                data["line_items"] = [
                    {
                        "id": item.id, 
                        "description": item.description_picking or "",
                        "quantity": item.product_uom_qty,
                        "product": {"id": item.product_id.id, "name": item.product_id.name, "code": item.product_id.default_code or "", "uom": item.product_id.uom_id.name} if item.product_id else {}
                    } for item in stock_picking.move_ids_without_package
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
                    data["line_items"] = [
                        {
                            "id": item.id, 
                            "description": item.description_picking or "",
                            "quantity": item.product_uom_qty,
                            "product": {"id": item.product_id.id, "name": item.product_id.name, "code": item.product_id.default_code or "", "uom": item.product_id.uom_id.name} if item.product_id else {}
                        } for item in stock_picking.move_ids_without_package
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