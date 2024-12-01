import logging
import pytz
from datetime import datetime, date, timedelta
from odoo import models, fields, api, _
from odoo.http import request
from odoo.exceptions import ValidationError, UserError


logger = logging.getLogger(__name__)


class NaidashCourier(models.Model):
    _inherit = "courier.custom"


    # Sender's Details
    sender_name_id = fields.Many2one(
        'res.partner',
        string = "Sender's Name",
        required = False
    )
    
    sender_street = fields.Text(
        string = "Sender's Street",
        required = False
    )
    
    sender_zip = fields.Char(
        string = "Sender's Zip Code",
        required = False
    )
    
    sender_city = fields.Char(
        string = "Sender's City",
        required = False
    )
    
    sender_state_id = fields.Many2one(
        "res.country.state",
        string = "Sender's State",
        domain = "[('country_id', '=', sender_country_id)]",
        required = False
    )
    
    sender_country_id = fields.Many2one(
        'res.country',
        string = "Sender's Country",
        required = False
    )
    
    sender_mobile = fields.Char(
        string = "Sender's Mobile No",
        required = False
    )
    
    sender_email = fields.Char(
        string = "Sender's Email",
        required = False
    )
    
    # Receiver's Details
    receiver_name_id = fields.Many2one(
        'res.partner',
        string = "Receiver's Name",
        required = False
    )
        
    receiver_name = fields.Char(
        string = "Receiver Name",
        required = False
    )
    
    receiver_street = fields.Text(
        string = "Receiver's Street",
        required = False
    )
    
    receiver_zip = fields.Char(
        string = "Receiver's Zip code",
        required = False
    )
    
    receiver_city = fields.Char(
        string = "Receiver's City",
        required = False
    )
    
    receiver_state = fields.Char(
        string = "Receiver's State",
        required = False
    )
    
    receiver_country = fields.Char(
        string = "Receiver's Country",
        required = False
    )
    
    receiver_mobile = fields.Char(
        string = "Receiver's Mobile No",
        required = False
    )
    
    receiver_email = fields.Char(
        string = "Receiver's Email",
        required = False
    )
    
    receiver_state_id = fields.Many2one(
        "res.country.state",
        string = "Receiver's State",
        domain = "[('country_id', '=', receiver_country_id)]",
        required = False
    )
    
    receiver_country_id = fields.Many2one(
        'res.country',
        string = "Receiver's Country",
        required = False
    )    
            
    is_drop_shipping = fields.Boolean(
        string = "Requires Dropshipping?",
        default = False,
        help="If set to true, dropshipping services are required otherwise the dropshipping services are not required"
    )
    
    is_receiver_invoice = fields.Boolean(
        string = "Invoice The Receiver?",
        default = True,
        help="If set to true, the receiver will be invoiced otherwise the sender will be invoiced"
    )
    
    distance = fields.Float(
        string = "Total Kilometres"
    )
        
    user_id = fields.Many2one(
        'res.users',
        string = "Responsible User",
        readonly = False
    )
    
    company_id = fields.Many2one(
        'res.company',
        string = "Company",
        related = "user_id.company_id",
        readonly = False
    )    
    
    @api.model
    def create(self, vals):        
        if vals.get('name', _('New')) == _('New'):
            milliseconds = (datetime.now()).strftime("%f")[:-3]
            created_date = fields.Datetime.context_timestamp(self, fields.Datetime.now()).strftime("%Y%m%d%H%M%S")
            vals['name'] = f"CR-{created_date}{milliseconds}"
        res = super(NaidashCourier, self).create(vals)
        return res
    
    @api.onchange('receiver_name_id')
    def onchange_receiver_contact_info_custom(self):
        if self.receiver_name_id:
            self.receiver_street = self.receiver_name_id.street
            self.receiver_street2 = self.receiver_name_id.street2
            self.receiver_city = self.receiver_name_id.city
            self.receiver_state_id = self.receiver_name_id.state_id
            self.receiver_zip = self.receiver_name_id.zip
            self.receiver_country_id = self.receiver_name_id.country_id
            self.receiver_mobile = self.receiver_name_id.phone
            self.receiver_email = self.receiver_name_id.email
            
    @api.depends('distance')
    def _compute_distance_charges(self):
        for rec in self:
            line = rec.env['distance.price.custom'].search([('min_value','<=',rec.distance), ('max_value','>=',rec.distance)], limit=1)
            rec.distance_product_id = line.product_id
            rec.distance_charges = line.cost

    @api.depends('priority_id.charges', 'total_courier_charges', 'distance_charges')
    def _compute_additional_charges(self):
        for rec in self:            
            rec.additional_charges = ((rec.total_courier_charges + rec.distance_charges) / 100) * rec.priority_id.charges            
    
    def create_courier_request(self, request_data):
        """Create Courier Request
        """
        
        try:
            vals = dict()
            data = dict()
            response_data = dict()
            items_to_transport = []            
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:                            
                search_param_values = ["", None]
                
                is_drop_shipping = request_data.get("is_drop_shipping")
                is_receiver_invoice = request_data.get("is_receiver_invoice")
                receiver_partner_id = request_data.get("receiver_partner_id")
                category_id = request_data.get("category_id")
                priority_id = request_data.get("priority_id")
                assigned_user_id = request_data.get("assigned_user_id")
                delivery_date = request_data.get("delivery_date")
                courier_type = request_data.get("courier_type")    
                tag_ids = request_data.get("tag_ids")
                distance = request_data.get("distance")
                description = request_data.get("description")
                internal_note = request_data.get("internal_note")
                sender_partner_id = request_data.get("sender_partner_id")
                line_items = request_data.get("line_items")                
                
                if not receiver_partner_id:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Missing receiver's partner id"
                    return response_data                              
                    
                if not category_id:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Missing category"
                    return response_data
                    
                if not priority_id:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Missing priority"
                    return response_data
                    
                if not assigned_user_id:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Missing user"
                    return response_data
                    
                if not tag_ids:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Missing tag"
                    return response_data
                    
                if not distance:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Missing distance"
                    return response_data
                    
                if not delivery_date:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Missing delivery date"
                    return response_data
                    
                if not courier_type:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Missing courier type"
                    return response_data                                                                                                                                                                  
                    
                if is_drop_shipping == True and sender_partner_id in search_param_values:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Missing sender's partner id"
                    return response_data
                    
                if is_drop_shipping == False and is_receiver_invoice == False:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Receiver must be invoiced"
                    return response_data
                    
                if is_drop_shipping == False and sender_partner_id:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Remove the sender's details"
                    return response_data 
                
                if not line_items:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Add items to transport"
                    return response_data
                
                if isinstance(tag_ids, list) == False:
                    response_data["code"] = 422
                    response_data["message"] = "Unprocessable Content! Expected a list of integer(s) in `tag_ids`"
                    return response_data                
                
                if isinstance(line_items, list) == False:
                    response_data["code"] = 422
                    response_data["message"] = "Unprocessable Content! Expected a list of objects in `line_items`"
                    return response_data
                
                if is_drop_shipping not in search_param_values:
                    vals["is_drop_shipping"] = is_drop_shipping
                        
                if is_receiver_invoice not in search_param_values:
                    vals["is_receiver_invoice"] = is_receiver_invoice                
                
                if assigned_user_id:
                    user = self.env['res.users'].browse(int(assigned_user_id))
                    
                    if user:
                        vals["user_id"] = user.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "User Not Found!"
                        return response_data

                if priority_id:
                    priority = self.env['courier.priority.custom'].browse(int(priority_id))
                    
                    if priority:
                        vals["priority_id"] = priority.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Priority Not Found!"
                        return response_data                
                
                if category_id:
                    category = self.env['courier.category.custom'].browse(int(category_id))
                    
                    if category:
                        vals["category_id"] = category.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Category Not Found!"
                        return response_data                                          
                
                if receiver_partner_id:
                    receiver = self.env['res.partner'].browse(int(receiver_partner_id))
                    
                    if receiver:
                        # Receiver's details
                        vals["receiver_name_id"] = receiver.id
                        vals["receiver_mobile"] = receiver.phone
                        vals["receiver_email"] = receiver.email
                        vals["receiver_country_id"] = receiver.country_id.id
                        vals["receiver_state_id"] = receiver.state_id.id
                        vals["receiver_street"] = receiver.street
                        
                        # Courier
                        vals["delivery_date"] = delivery_date
                        vals["courier_type"] = courier_type
                        
                        # Internal                        
                        vals["distance"] = float(distance)
                        vals["description"] = description
                        vals["internal_note"] = internal_note
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Receiver Not Found!"
                        return response_data                        
                
                if sender_partner_id:
                    sender = self.env['res.partner'].browse(int(sender_partner_id))
                
                    if sender:
                        # Sender's details
                        vals["sender_name_id"] = sender.id
                        vals["sender_mobile"] = sender.phone
                        vals["sender_email"] = sender.email
                        vals["sender_country_id"] = sender.country_id.id
                        vals["sender_state_id"] = sender.state_id.id
                        vals["sender_street"] = sender.street
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Sender Not Found!"
                        return response_data
                    
                if tag_ids:
                    tags = self.env['courier.tag.custom'].browse(tag_ids)
                    
                    if tags:
                        vals["tag_ids"] = [tag.id for tag in tags]
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Tag Not Found!"
                        return response_data
                    
                if line_items:
                    product = self.env['product.product'].search(
                        [
                            ('name', '=', 'Courier Service'),
                            ('default_code', '=', 'CS1'),
                        ], order="id asc", limit=1
                    ).id
                    
                    if product:
                        for item in line_items:
                            courier_items = {
                                "product_id": product,
                                "name": item.get("name"),
                                "qty": int(item.get("quantity")) if item.get("quantity") else 1,
                                "weight": float(item.get("weight")) if item.get("weight") else 0.0,
                                "box_id": False if not item.get("dimension_id") else int(item.get("dimension_id"))
                            }
                            
                            items_to_transport.append((0, 0, courier_items))
                            
                        vals["courier_line_ids"] = items_to_transport
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Setup the `Courier Service` product"
                        return response_data
                    
                # Create courier request
                courier = self.env['courier.custom'].create(vals)                

                if courier:
                    data['id'] = courier.id
                    response_data["code"] = 201                
                    response_data["message"] = "Request created successfully"
                    response_data["data"] = data
            else:
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except TypeError as e:
            logger.error(f"Datatype error ocurred while creating the courier request:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while creating the courier request:\n\n{str(e)}")
            raise e
        
    def edit_courier_request(self, courier_id, request_data):
        """Edit the Courier Request details
        """
        
        try:
            response_data = dict()
            courier_details = dict()                
            items_to_transport = []            
            search_param_values = ["", None, []]
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            is_record_active = request_data.get("is_record_active")
            is_drop_shipping = request_data.get("is_drop_shipping")
            is_receiver_invoice = request_data.get("is_receiver_invoice")
            receiver_partner_id = request_data.get("receiver_partner_id")
            stage_id = request_data.get("stage_id")
            category_id = request_data.get("category_id")
            priority_id = request_data.get("priority_id")
            assigned_user_id = request_data.get("assigned_user_id")
            delivery_date = request_data.get("delivery_date")
            courier_type = request_data.get("courier_type")    
            tag_ids = request_data.get("tag_ids")
            distance = request_data.get("distance")
            description = request_data.get("description")
            internal_note = request_data.get("internal_note")
            sender_partner_id = request_data.get("sender_partner_id")
            line_items = request_data.get("line_items")
            
            if is_courier_manager:                
                courier = self.env['courier.custom'].search(
                    [
                        ('id','=', int(courier_id)), '|', 
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if courier:
                    if is_drop_shipping == True and sender_partner_id in search_param_values:
                        response_data["code"] = 400
                        response_data["message"] = "Bad Request! Missing sender's partner id"
                        return response_data
                        
                    if is_drop_shipping == False and is_receiver_invoice == False:
                        response_data["code"] = 400
                        response_data["message"] = "Bad Request! Receiver must be invoiced"
                        return response_data
                        
                    if is_drop_shipping == False and sender_partner_id:
                        response_data["code"] = 400
                        response_data["message"] = "Bad Request! Remove the sender's details"
                        return response_data
                    
                    if is_record_active not in search_param_values:
                        courier_details["active"] = is_record_active                        
                    
                    if distance not in search_param_values:
                        courier_details["distance"] = float(distance)
                        
                    if delivery_date not in search_param_values:
                        courier_details["delivery_date"] = delivery_date
                        
                    if courier_type not in search_param_values:
                        courier_details["courier_type"] = courier_type
                        
                    if description not in search_param_values:
                        courier_details["description"] = description
                        
                    if internal_note not in search_param_values:
                        courier_details["internal_note"] = internal_note                                        
                    
                    if is_drop_shipping not in search_param_values:
                        courier_details["is_drop_shipping"] = is_drop_shipping
                            
                    if is_receiver_invoice not in search_param_values:
                        courier_details["is_receiver_invoice"] = is_receiver_invoice                
                    
                    if stage_id not in search_param_values:
                        stage = self.env['courier.stage.custom'].search(
                            [
                                ('id','=', int(stage_id)), '|', 
                                ('active','=', True), ('active','=', False)
                            ]
                        )
                        
                        if stage:
                            courier_details["stage_id"] = stage.id
                        else:
                            response_data["code"] = 404
                            response_data["message"] = "Stage Not Found!"
                            return response_data                    
                    
                    if assigned_user_id not in search_param_values:
                        user = self.env['res.users'].browse(int(assigned_user_id))                        
                        if user:
                            courier_details["user_id"] = user.id
                        else:
                            response_data["code"] = 404
                            response_data["message"] = "User Not Found!"
                            return response_data

                    if priority_id not in search_param_values:
                        priority = self.env['courier.priority.custom'].browse(int(priority_id))                        
                        if priority:
                            courier_details["priority_id"] = priority.id
                        else:
                            response_data["code"] = 404
                            response_data["message"] = "Priority Not Found!"
                            return response_data                
                    
                    if category_id not in search_param_values:
                        category = self.env['courier.category.custom'].browse(int(category_id))                        
                        if category:
                            courier_details["category_id"] = category.id
                        else:
                            response_data["code"] = 404
                            response_data["message"] = "Category Not Found!"
                            return response_data                                          
                    
                    if receiver_partner_id not in search_param_values:
                        receiver = self.env['res.partner'].browse(int(receiver_partner_id))                        
                        if receiver:
                            # Receiver's details
                            courier_details["receiver_name_id"] = receiver.id
                            courier_details["receiver_mobile"] = receiver.phone
                            courier_details["receiver_email"] = receiver.email
                            courier_details["receiver_country_id"] = receiver.country_id.id
                            courier_details["receiver_state_id"] = receiver.state_id.id
                            courier_details["receiver_street"] = receiver.street                                                
                        else:
                            response_data["code"] = 404
                            response_data["message"] = "Receiver Not Found!"
                            return response_data                        
                    
                    if sender_partner_id not in search_param_values:
                        sender = self.env['res.partner'].browse(int(sender_partner_id))                    
                        if sender:
                            # Sender's details
                            courier_details["sender_name_id"] = sender.id
                            courier_details["sender_mobile"] = sender.phone
                            courier_details["sender_email"] = sender.email
                            courier_details["sender_country_id"] = sender.country_id.id
                            courier_details["sender_state_id"] = sender.state_id.id
                            courier_details["sender_street"] = sender.street
                        else:
                            response_data["code"] = 404
                            response_data["message"] = "Sender Not Found!"
                            return response_data
                        
                    if tag_ids not in search_param_values:
                        tags = self.env['courier.tag.custom'].browse(tag_ids)                        
                        if tags:
                            courier_details["tag_ids"] = [tag.id for tag in tags]
                        else:
                            response_data["code"] = 404
                            response_data["message"] = "Tag Not Found!"
                            return response_data
                     
                    product = self.env['product.product'].search(
                        [
                            ('name', '=', 'Courier Service'),
                            ('default_code', '=', 'CS1'),
                        ], order="id asc", limit=1
                    ).id
                    
                    if product:
                        if line_items not in search_param_values:                            
                            for item in line_items:
                                if item.get("id"):
                                    update_courier_item_vals = dict()
                                    
                                    if item.get("product_id") not in search_param_values:
                                        update_courier_item_vals["product_id"] = int(item.get("product_id"))
                                    if item.get("name") not in search_param_values:
                                        update_courier_item_vals["name"] = item.get("name")
                                    if item.get("quantity") not in search_param_values:
                                        update_courier_item_vals["qty"] = int(item.get("quantity"))
                                    if item.get("weight") not in search_param_values:
                                        update_courier_item_vals["weight"] = float(item.get("weight"))
                                    if item.get("dimension_id") not in search_param_values:
                                        update_courier_item_vals["box_id"] = int(item.get("dimension_id"))
                                      
                                    item_id = item.get("id")    
                                    
                                    # Check if there are any courier line items to be deleted/removed
                                    if item.get("delete_record") == True:
                                        items_to_transport.append((2, int(item_id)))
                                    
                                    # Check if there are any courier line items to be updated
                                    if item.get("delete_record") == False and update_courier_item_vals:
                                        items_to_transport.append((1, int(item_id), update_courier_item_vals))
                                else:
                                    create_courier_item_vals = {
                                        "product_id": product,
                                        "name": item.get("name"),
                                        "qty": int(item.get("quantity")) if item.get("quantity") else 1,
                                        "weight": float(item.get("weight")) if item.get("weight") else 0.0,
                                        "box_id": False if not item.get("dimension_id") else int(item.get("dimension_id"))
                                    }
                                                                        
                                    # Create the Courier line items
                                    items_to_transport.append((0, 0, create_courier_item_vals))                                
                                
                            if items_to_transport:
                                courier_details["courier_line_ids"] = items_to_transport
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Setup the `Courier Service` product"
                        return response_data
                                            
                    # Update courier details
                    if courier_details:                        
                        courier.write(courier_details)
                        response_data["code"] = 200                
                        response_data["message"] = "Courier updated successfully"
                        return response_data
                    else:
                        response_data["code"] = 204                
                        response_data["message"] = "Nothing to update"
                        return response_data 
                else:
                    response_data["code"] = 404               
                    response_data["message"] = "Courier Not Found!"
                    return response_data                         
            else:
                logged_in_user = self.env.user
                # Other users will access active courier requests only
                active_courier = self.env['courier.custom'].search(
                    [
                        ('id', '=', int(courier_id)),
                        ('user_id', '=', logged_in_user.id)
                    ]
                )
                
                if active_courier:
                    if stage_id not in search_param_values:
                        stage = self.env['courier.stage.custom'].browse(int(stage_id))                        
                        if stage:
                            courier_details["stage_id"] = stage.id
                        else:
                            response_data["code"] = 404
                            response_data["message"] = "Stage Not Found!"
                            return response_data
                        
                    # Update courier details
                    if courier_details:
                        active_courier.write(courier_details)
                        response_data["code"] = 200                
                        response_data["message"] = "Courier updated successfully"
                        return response_data
                    else:
                        response_data["code"] = 204                
                        response_data["message"] = "Nothing to update"
                        return response_data
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Courier Not Found!"
            
            return response_data
        except TypeError as e:
            logger.error(f"Datatype error ocurred while modifying the courier details:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while modifying the courier details:\n\n{str(e)}")
            raise e
        
    def get_a_courier_request(self, courier_id):
        """Get the courier details
        """        
        
        try:
            data = dict()            
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for 
            # any courier request regardless of the active status
            if is_courier_manager:
                courier = self.env['courier.custom'].search(
                    [
                        ('id','=', int(courier_id)), '|', 
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if courier:
                    data["id"] = courier.id
                    data["name"] = courier.name
                    data["is_record_active"] = courier.active
                    data["is_receiver_invoice"] = courier.is_receiver_invoice
                    data["is_drop_shipping"] = courier.is_drop_shipping
                    data["courier_type"] = courier.courier_type
                    data["distance"] = courier.distance
                    data["is_readonly"] = courier.is_readonly
                    data["is_saleorder"] = courier.is_saleorder
                    data["courier_charges"] = courier.total_courier_charges
                    data["distance_charges"] = courier.distance_charges
                    data["additional_charges"] = courier.additional_charges
                    data["total_charges"] = courier.total
                    data["description"] = courier.description
                    data["internal_note"] = courier.internal_note
                    data["delivery_date"] = ""
                    
                    # Display the delivery time using the assigned user's local timezone
                    if courier.delivery_date:
                        assigned_user_timezone = courier.user_id.tz or pytz.utc
                        assigned_user_timezone = pytz.timezone(assigned_user_timezone)
                        delivery_date = (courier.delivery_date).strftime("%Y-%m-%d %H:%M")
                        delivery_date = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(delivery_date, "%Y-%m-%d %H:%M")).astimezone(assigned_user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["delivery_date"] = delivery_date
                    data["stage"] = {"id": courier.stage_id.id, "name": courier.stage_id.name} if courier.stage_id else {}
                    data["assigned_user"] = {"id": courier.user_id.id, "name": courier.user_id.name} if courier.user_id else {}
                    data["priority"] = {"id": courier.priority_id.id, "name": courier.priority_id.name} if courier.priority_id else {}
                    data["category_id"] = {"id": courier.category_id.id, "name": courier.category_id.name} if courier.category_id else {}
                    data["tag_ids"] = [{"id": tag.id, "name": tag.name} for tag in courier.tag_ids] if courier.tag_ids else []                    
                    data["distance_product"] = {"id": courier.distance_product_id.id, "name": courier.distance_product_id.name} if courier.distance_product_id else {}
                    data["additional_product"] = {"id": courier.additional_product_id.id, "name": courier.additional_product_id.name} if courier.additional_product_id else {}
                    data["sales_order"] = {"id": courier.sale_order_id.id, "name": courier.sale_order_id.name} if courier.sale_order_id else {}
                    data["currency"] = {"id": courier.currency_id.id, "name": courier.currency_id.name} if courier.currency_id else {}
                    data["company"] = {"id": courier.company_id.id, "name": courier.company_id.name} if courier.company_id else {}                    
                                        
                    data["receiver"] = {
                        "id": courier.receiver_name_id.id, 
                        "name": courier.receiver_name_id.name,
                        "phone": courier.receiver_mobile,
                        "email": courier.receiver_email,
                        "country": {"id": courier.receiver_country_id.id, "name": courier.receiver_country_id.name} if courier.receiver_country_id else {},
                        "state": {"id": courier.receiver_state_id.id, "name": courier.receiver_state_id.name} if courier.receiver_state_id else {},
                        "address": courier.receiver_street
                    } if courier.receiver_name_id else {}
                    
                    data["sender"] = {
                        "id": courier.sender_name_id.id, 
                        "name": courier.sender_name_id.name,
                        "phone": courier.sender_mobile,
                        "email": courier.sender_email,
                        "country": {"id": courier.sender_country_id.id, "name": courier.sender_country_id.name} if courier.sender_country_id else {},
                        "state": {"id": courier.sender_state_id.id, "name": courier.sender_state_id.name} if courier.sender_state_id else {},
                        "address": courier.sender_street                        
                    } if courier.sender_name_id else {}

                    data["line_items"] = [
                        {
                            "id": item.id, 
                            "name": item.name,
                            "quantity": item.qty,
                            "weight": item.weight,
                            "total_weight": item.total_weight,
                            "weight_cost": item.weight_cost,
                            "volumetric_weight": item.volumetric_weight,
                            "total_volumetric_weight": item.total_volumetric_weight,
                            "volumetric_weight_cost": item.volumetric_weight_cost,
                            "delete_record": False,
                            "subtotal": item.courier_subtotal,
                            "dimension": {"id": item.box_id.id, "name": item.box_id.name} if item.box_id else {},
                            "product": {"id": item.product_id.id, "name": item.product_id.name, "code": item.product_id.default_code or ""} if item.product_id else {}
                        } for item in courier.courier_line_ids
                    ] if courier.courier_line_ids else []
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = data
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Courier Not Found!"
            else:
                logged_in_user = self.env.user.id
                # Other users will access active courier 
                # requests assigned to them
                active_courier = self.env['courier.custom'].search(
                    [
                        ('id', '=', int(courier_id)),
                        ('user_id', '=', logged_in_user)
                    ]
                )
                
                if active_courier:
                    data["id"] = active_courier.id
                    data["name"] = active_courier.name
                    data["is_record_active"] = active_courier.active                    
                    data["is_receiver_invoice"] = active_courier.is_receiver_invoice
                    data["is_drop_shipping"] = active_courier.is_drop_shipping
                    data["courier_type"] = active_courier.courier_type
                    data["distance"] = active_courier.distance
                    data["is_readonly"] = active_courier.is_readonly
                    data["is_saleorder"] = active_courier.is_saleorder
                    data["courier_charges"] = active_courier.total_courier_charges
                    data["distance_charges"] = active_courier.distance_charges
                    data["additional_charges"] = active_courier.additional_charges
                    data["total_charges"] = active_courier.total
                    data["description"] = active_courier.description
                    data["internal_note"] = active_courier.internal_note
                    data["delivery_date"] = ""
                    
                    # Display the delivery time using the assigned user's local timezone
                    if active_courier.delivery_date:
                        assigned_user_timezone = active_courier.user_id.tz or pytz.utc
                        assigned_user_timezone = pytz.timezone(assigned_user_timezone)
                        delivery_date = (active_courier.delivery_date).strftime("%Y-%m-%d %H:%M")
                        delivery_date = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(delivery_date, "%Y-%m-%d %H:%M")).astimezone(assigned_user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["delivery_date"] = delivery_date
                    data["stage"] = {"id": active_courier.stage_id.id, "name": active_courier.stage_id.name} if active_courier.stage_id else {}
                    data["assigned_user"] = {"id": active_courier.user_id.id, "name": active_courier.user_id.name} if active_courier.user_id else {}
                    data["priority"] = {"id": active_courier.priority_id.id, "name": active_courier.priority_id.name} if active_courier.priority_id else {}
                    data["category_id"] = {"id": active_courier.category_id.id, "name": active_courier.category_id.name} if active_courier.category_id else {}
                    data["tag_ids"] = [{"id": tag.id, "name": tag.name} for tag in active_courier.tag_ids] if active_courier.tag_ids else []                    
                    data["distance_product"] = {"id": active_courier.distance_product_id.id, "name": active_courier.distance_product_id.name} if active_courier.distance_product_id else {}
                    data["additional_product"] = {"id": active_courier.additional_product_id.id, "name": active_courier.additional_product_id.name} if active_courier.additional_product_id else {}
                    data["sales_order"] = {"id": active_courier.sale_order_id.id, "name": active_courier.sale_order_id.name} if active_courier.sale_order_id else {}
                    data["currency"] = {"id": active_courier.currency_id.id, "name": active_courier.currency_id.name} if active_courier.currency_id else {}
                    data["company"] = {"id": active_courier.company_id.id, "name": active_courier.company_id.name} if active_courier.company_id else {}                    
                                        
                    data["receiver"] = {
                        "id": active_courier.receiver_name_id.id, 
                        "name": active_courier.receiver_name_id.name,
                        "phone": active_courier.receiver_mobile,
                        "email": active_courier.receiver_email,
                        "country": {"id": active_courier.receiver_country_id.id, "name": active_courier.receiver_country_id.name} if active_courier.receiver_country_id else {},
                        "state": {"id": active_courier.receiver_state_id.id, "name": active_courier.receiver_state_id.name} if active_courier.receiver_state_id else {},
                        "address": active_courier.receiver_street
                    } if active_courier.receiver_name_id else {}
                    
                    data["sender"] = {
                        "id": active_courier.sender_name_id.id, 
                        "name": active_courier.sender_name_id.name,
                        "phone": active_courier.sender_mobile,
                        "email": active_courier.sender_email,
                        "country": {"id": active_courier.sender_country_id.id, "name": active_courier.sender_country_id.name} if active_courier.sender_country_id else {},
                        "state": {"id": active_courier.sender_state_id.id, "name": active_courier.sender_state_id.name} if active_courier.sender_state_id else {},
                        "address": active_courier.sender_street                        
                    } if active_courier.sender_name_id else {}

                    data["line_items"] = [
                        {
                            "id": item.id, 
                            "name": item.name,
                            "quantity": item.qty,
                            "weight": item.weight,
                            "total_weight": item.total_weight,
                            "weight_cost": item.weight_cost,
                            "volumetric_weight": item.volumetric_weight,
                            "total_volumetric_weight": item.total_volumetric_weight,
                            "volumetric_weight_cost": item.volumetric_weight_cost,
                            "subtotal": item.courier_subtotal,
                            "delete_record": False,
                            "dimension": {"id": item.box_id.id, "name": item.box_id.name} if item.box_id else {},
                            "product": {"id": item.product_id.id, "name": item.product_id.name, "code": item.product_id.default_code or ""} if item.product_id else {}
                        } for item in active_courier.courier_line_ids
                    ] if active_courier.courier_line_ids else []                 
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = data
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Courier Not Found!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the courier details:\n\n{str(e)}")
            raise e
        
    def get_all_courier_requests(self, request_data):
        """Get all the courier requests
        """        
        
        try:
            response_data = dict()
            query_params = list()
            all_courier_requests = []
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if request_data.get("phone"):
                query_params = [
                    '|',
                    ('sender_mobile','=', request_data.get("phone")),
                    ('receiver_mobile','=', request_data.get("phone")),
                ]
                
            if request_data.get("delivery_date"):
                delivery_date = request_data.get("delivery_date")
                query_params = [
                    ('delivery_date','<=',(datetime(delivery_date.year, delivery_date.month, delivery_date.day)).strftime('%Y-%m-%d 23:59:59')),
                    ('delivery_date','>=',(datetime(delivery_date.year, delivery_date.month, delivery_date.day)).strftime('%Y-%m-%d 00:00:00'))
                ] 
                
            if request_data.get("stage_id"):
                query_params = [
                    ('stage_id','=', request_data.get("stage_id"))
                ] 
                
            if request_data.get("priority_id"):
                query_params = [
                    ('priority_id','=', request_data.get("priority_id"))
                ]
                 
            if request_data.get("category_id"):
                query_params = [
                    ('category_id','=', request_data.get("category_id"))
                ]
                                
            if request_data.get("courier_type"):
                query_params = [
                    ('courier_type','=', request_data.get("courier_type"))
                ]
            
            if request_data.get("is_drop_shipping") == True or request_data.get("is_drop_shipping") == False:
                query_params = [
                    ('is_drop_shipping','=', request_data.get("is_drop_shipping"))
                ]
                                                                                                                                                            
            # Courier Admins/Managers can search
            # for any courier request
            if is_courier_manager:
                if request_data.get("assigned_user_id"):
                    query_params = [
                        ('user_id','=', request_data.get("assigned_user_id"))
                    ]
                    
                if request_data.get("is_record_active") == True or request_data.get("is_record_active") == False:
                    query_params = [
                        ('active','=', request_data.get("is_record_active"))
                    ]
                                                   
                couriers = self.env['courier.custom'].search(query_params, order='id desc')
                
                if couriers:
                    for courier in couriers:
                        data = dict()                    
                        data["id"] = courier.id
                        data["name"] = courier.name
                        data["is_record_active"] = courier.active
                        data["is_receiver_invoice"] = courier.is_receiver_invoice
                        data["is_drop_shipping"] = courier.is_drop_shipping
                        data["courier_type"] = courier.courier_type
                        data["distance"] = courier.distance
                        data["is_readonly"] = courier.is_readonly
                        data["is_saleorder"] = courier.is_saleorder
                        data["courier_charges"] = courier.total_courier_charges
                        data["distance_charges"] = courier.distance_charges
                        data["additional_charges"] = courier.additional_charges
                        data["total_charges"] = courier.total
                        data["description"] = courier.description
                        data["internal_note"] = courier.internal_note
                        data["delivery_date"] = ""
                        
                        # Display the delivery time using the assigned user's local timezone
                        if courier.delivery_date:
                            assigned_user_timezone = courier.user_id.tz or pytz.utc
                            assigned_user_timezone = pytz.timezone(assigned_user_timezone)
                            delivery_date = (courier.delivery_date).strftime("%Y-%m-%d %H:%M")
                            delivery_date = datetime.strftime(
                                pytz.utc.localize(datetime.strptime(delivery_date, "%Y-%m-%d %H:%M")).astimezone(assigned_user_timezone),
                                "%Y-%m-%d %H:%M"
                            )
                            
                            data["delivery_date"] = delivery_date
                            
                        data["stage"] = {"id": courier.stage_id.id, "name": courier.stage_id.name} if courier.stage_id else {}
                        data["assigned_user"] = {"id": courier.user_id.id, "name": courier.user_id.name} if courier.user_id else {}
                        data["priority"] = {"id": courier.priority_id.id, "name": courier.priority_id.name} if courier.priority_id else {}
                        data["category_id"] = {"id": courier.category_id.id, "name": courier.category_id.name} if courier.category_id else {}
                        data["tag_ids"] = [{"id": tag.id, "name": tag.name} for tag in courier.tag_ids] if courier.tag_ids else []                    
                        data["distance_product"] = {"id": courier.distance_product_id.id, "name": courier.distance_product_id.name} if courier.distance_product_id else {}
                        data["additional_product"] = {"id": courier.additional_product_id.id, "name": courier.additional_product_id.name} if courier.additional_product_id else {}
                        data["sales_order"] = {"id": courier.sale_order_id.id, "name": courier.sale_order_id.name} if courier.sale_order_id else {}
                        data["currency"] = {"id": courier.currency_id.id, "name": courier.currency_id.name} if courier.currency_id else {}
                        data["company"] = {"id": courier.company_id.id, "name": courier.company_id.name} if courier.company_id else {}                    
                                            
                        data["receiver"] = {
                            "id": courier.receiver_name_id.id, 
                            "name": courier.receiver_name_id.name,
                            "phone": courier.receiver_mobile,
                            "email": courier.receiver_email,
                            "country": {"id": courier.receiver_country_id.id, "name": courier.receiver_country_id.name} if courier.receiver_country_id else {},
                            "state": {"id": courier.receiver_state_id.id, "name": courier.receiver_state_id.name} if courier.receiver_state_id else {},
                            "address": courier.receiver_street
                        } if courier.receiver_name_id else {}
                        
                        data["sender"] = {
                            "id": courier.sender_name_id.id, 
                            "name": courier.sender_name_id.name,
                            "phone": courier.sender_mobile,
                            "email": courier.sender_email,
                            "country": {"id": courier.sender_country_id.id, "name": courier.sender_country_id.name} if courier.sender_country_id else {},
                            "state": {"id": courier.sender_state_id.id, "name": courier.sender_state_id.name} if courier.sender_state_id else {},
                            "address": courier.sender_street                        
                        } if courier.sender_name_id else {}

                        data["line_items"] = [
                            {
                                "id": item.id, 
                                "name": item.name,
                                "quantity": item.qty,
                                "weight": item.weight,
                                "total_weight": item.total_weight,
                                "weight_cost": item.weight_cost,
                                "volumetric_weight": item.volumetric_weight,
                                "total_volumetric_weight": item.total_volumetric_weight,
                                "volumetric_weight_cost": item.volumetric_weight_cost,
                                "subtotal": item.courier_subtotal,
                                "delete_record": False,
                                "dimension": {"id": item.box_id.id, "name": item.box_id.name} if item.box_id else {},
                                "product": {"id": item.product_id.id, "name": item.product_id.name, "code": item.product_id.default_code or ""} if item.product_id else {}
                            } for item in courier.courier_line_ids
                        ] if courier.courier_line_ids else []
                        
                        all_courier_requests.append(data)
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = all_courier_requests
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Courier Not Found!"
            else: 
                logged_in_user = self.env.user.id
                query_params.append(('user_id','=', logged_in_user))
                # Other users will access active courier 
                # requests assigned to them
                active_couriers = self.env['courier.custom'].search(query_params, order='id asc')
                
                if active_couriers:
                    for active_courier in active_couriers:
                        data = dict()
                        data["id"] = active_courier.id
                        data["name"] = active_courier.name
                        data["is_record_active"] = active_courier.active                    
                        data["is_receiver_invoice"] = active_courier.is_receiver_invoice
                        data["is_drop_shipping"] = active_courier.is_drop_shipping
                        data["courier_type"] = active_courier.courier_type
                        data["distance"] = active_courier.distance
                        data["is_readonly"] = active_courier.is_readonly
                        data["is_saleorder"] = active_courier.is_saleorder
                        data["courier_charges"] = active_courier.total_courier_charges
                        data["distance_charges"] = active_courier.distance_charges
                        data["additional_charges"] = active_courier.additional_charges
                        data["total_charges"] = active_courier.total
                        data["description"] = active_courier.description
                        data["internal_note"] = active_courier.internal_note                        
                        data["delivery_date"] = ""
                        
                        # Display the delivery time using the assigned user's local timezone
                        if active_courier.delivery_date:
                            assigned_user_timezone = active_courier.user_id.tz or pytz.utc
                            assigned_user_timezone = pytz.timezone(assigned_user_timezone)
                            delivery_date = (active_courier.delivery_date).strftime("%Y-%m-%d %H:%M")
                            delivery_date = datetime.strftime(
                                pytz.utc.localize(datetime.strptime(delivery_date, "%Y-%m-%d %H:%M")).astimezone(assigned_user_timezone),
                                "%Y-%m-%d %H:%M"
                            )
                            
                            data["delivery_date"] = delivery_date
                        data["stage"] = {"id": active_courier.stage_id.id, "name": active_courier.stage_id.name} if active_courier.stage_id else {}
                        data["assigned_user"] = {"id": active_courier.user_id.id, "name": active_courier.user_id.name} if active_courier.user_id else {}
                        data["priority"] = {"id": active_courier.priority_id.id, "name": active_courier.priority_id.name} if active_courier.priority_id else {}
                        data["category_id"] = {"id": active_courier.category_id.id, "name": active_courier.category_id.name} if active_courier.category_id else {}
                        data["tag_ids"] = [{"id": tag.id, "name": tag.name} for tag in active_courier.tag_ids] if active_courier.tag_ids else []                    
                        data["distance_product"] = {"id": active_courier.distance_product_id.id, "name": active_courier.distance_product_id.name} if active_courier.distance_product_id else {}
                        data["additional_product"] = {"id": active_courier.additional_product_id.id, "name": active_courier.additional_product_id.name} if active_courier.additional_product_id else {}
                        data["sales_order"] = {"id": active_courier.sale_order_id.id, "name": active_courier.sale_order_id.name} if active_courier.sale_order_id else {}
                        data["currency"] = {"id": active_courier.currency_id.id, "name": active_courier.currency_id.name} if active_courier.currency_id else {}
                        data["company"] = {"id": active_courier.company_id.id, "name": active_courier.company_id.name} if active_courier.company_id else {}                    
                                            
                        data["receiver"] = {
                            "id": active_courier.receiver_name_id.id, 
                            "name": active_courier.receiver_name_id.name,
                            "phone": active_courier.receiver_mobile,
                            "email": active_courier.receiver_email,
                            "country": {"id": active_courier.receiver_country_id.id, "name": active_courier.receiver_country_id.name} if active_courier.receiver_country_id else {},
                            "state": {"id": active_courier.receiver_state_id.id, "name": active_courier.receiver_state_id.name} if active_courier.receiver_state_id else {},
                            "address": active_courier.receiver_street
                        } if active_courier.receiver_name_id else {}
                        
                        data["sender"] = {
                            "id": active_courier.sender_name_id.id, 
                            "name": active_courier.sender_name_id.name,
                            "phone": active_courier.sender_mobile,
                            "email": active_courier.sender_email,
                            "country": {"id": active_courier.sender_country_id.id, "name": active_courier.sender_country_id.name} if active_courier.sender_country_id else {},
                            "state": {"id": active_courier.sender_state_id.id, "name": active_courier.sender_state_id.name} if active_courier.sender_state_id else {},
                            "address": active_courier.sender_street                        
                        } if active_courier.sender_name_id else {}

                        data["line_items"] = [
                            {
                                "id": item.id, 
                                "name": item.name,
                                "quantity": item.qty,
                                "weight": item.weight,
                                "total_weight": item.total_weight,
                                "weight_cost": item.weight_cost,
                                "volumetric_weight": item.volumetric_weight,
                                "total_volumetric_weight": item.total_volumetric_weight,
                                "volumetric_weight_cost": item.volumetric_weight_cost,
                                "subtotal": item.courier_subtotal,
                                "delete_record": False,
                                "dimension": {"id": item.box_id.id, "name": item.box_id.name} if item.box_id else {},
                                "product": {"id": item.product_id.id, "name": item.product_id.name, "code": item.product_id.default_code or ""} if item.product_id else {}
                            } for item in active_courier.courier_line_ids
                        ] if active_courier.courier_line_ids else []
                                            
                        all_courier_requests.append(data)
                        
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = all_courier_requests
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Courier Not Found!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the courier details:\n\n{str(e)}")
            raise e
        
    def move_to_next_stage(self, courier_id):
        """Moves a Courier request to the next stage"""

        logged_in_user = self.env.user.id 
        response_data = dict()

        try:
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:
                courier = self.env['courier.custom'].search(
                    [
                        ('id', '=', int(courier_id))
                    ]
                )
                
                if courier:
                    current_stage = courier.stage_id
                    # Get the next stage if the current stage is neither marked as `last` nor `cancel`
                    if courier.stage_id.is_last_stage == False or courier.stage_id.is_cancel_stage == False:
                        next_stage = self.env['courier.stage.custom'].search(
                            [
                                ('stage_sequence', '>', current_stage.stage_sequence)
                            ], 
                            order='stage_sequence asc', limit=1
                        )

                        if next_stage:
                            courier.write({"stage_id": next_stage.id})
                            response_data["code"] = 200
                            response_data["message"] = f"successfully moved to {courier.stage_id.name}!"
                        else:
                            response_data["code"] = 404
                            response_data["message"] = "Stage not found!"
                    else:
                        response_data["code"] = 403
                        response_data["message"] = f"{self.env.user.name}, This action is forbidden!"
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Courier not found!"
            else:
                active_courier = self.env['courier.custom'].search(
                    [
                        ('id', '=', int(courier_id)),
                        ('user_id', '=', logged_in_user)
                    ]
                )
                
                if active_courier:
                    current_stage = active_courier.stage_id
                    # Get the next stage if the current stage is neither marked as `last` nor `cancel`
                    if active_courier.stage_id.is_last_stage == False or active_courier.stage_id.is_cancel_stage == False:
                        next_stage = self.env['courier.stage.custom'].search(
                            [
                                ('stage_sequence', '>', current_stage.stage_sequence)
                            ], 
                            order='stage_sequence asc', limit=1
                        )

                        if next_stage:
                            active_courier.write({"stage_id": next_stage.id})
                            response_data["code"] = 200
                            response_data["message"] = f"successfully moved to {active_courier.stage_id.name}!"
                        else:
                            response_data["code"] = 404
                            response_data["message"] = "Stage not found!"
                    else:
                        response_data["code"] = 403
                        response_data["message"] = f"{self.env.user.name}, This action is forbidden!"
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Courier not found!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while updating the courier request:\n\n{str(e)}")
            raise e