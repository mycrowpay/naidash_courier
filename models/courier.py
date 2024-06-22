import logging

from datetime import datetime
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
                
                if isinstance(tag_ids, list) == False :
                    response_data["code"] = 422
                    response_data["message"] = "Unprocessable Content! Expected a list of integer(s) in `tag_ids`"
                    return response_data                
                
                if isinstance(line_items, list) == False :
                    response_data["code"] = 422
                    response_data["message"] = "Unprocessable Content! Expected a list of objects in `line_items`"
                    return response_data
                
                if is_drop_shipping not in search_param_values:
                    vals["is_drop_shipping"] = is_drop_shipping
                        
                if is_receiver_invoice not in search_param_values:
                    vals["is_receiver_invoice"] = is_receiver_invoice                
                
                if assigned_user_id:
                    user = self.env['res.users'].search(
                        [
                            ('id','=', int(assigned_user_id))
                        ]
                    )                    
                    
                    if user:
                        vals["user_id"] = user.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "User Not Found!"
                        return response_data

                if priority_id:
                    priority = self.env['courier.priority.custom'].search(
                        [
                            ('id','=', int(priority_id))
                        ]
                    )                    
                    
                    if priority:
                        vals["priority_id"] = priority.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Priority Not Found!"
                        return response_data                
                
                if category_id:
                    category = self.env['courier.category.custom'].search(
                        [
                            ('id','=', int(category_id))
                        ]
                    )                    
                    
                    if category:
                        vals["category_id"] = category.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Category Not Found!"
                        return response_data                                          
                
                if receiver_partner_id:
                    receiver = self.env['res.partner'].search(
                        [
                            ('id','=', int(receiver_partner_id))
                        ]
                    )                    
                    
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
                    sender = self.env['res.partner'].search(
                        [
                            ('id','=', int(sender_partner_id))
                        ]
                    )
                
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
                    tag_list = []
                    tags = self.env['courier.tag.custom'].search(
                        [
                            ('id','in', tag_ids)
                        ]
                    )                   
                    
                    if tags:
                        for tag in tags:
                            tag_list.append(tag.id)
                        vals["tag_ids"] = tag_list
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Tag Not Found!"
                        return response_data
                    
                if line_items:
                    product = self.env['product.product'].search(
                        [
                            ('name', '=', 'Courier Service'),
                            ('default_code', '=', 'CS1'),
                        ], order="id desc", limit=1
                    ).id
                    
                    if product:
                        for item in line_items:
                            courier_items = {
                                "product_id": product,
                                "name": item.get("name"),
                                "qty": int(item.get("quantity")) if item.get("quantity") else 1,
                                "weight": float(item.get("weight")) if item.get("weight") else 0.0,
                                "box_id": int(item.get("dimension_id")) if item.get("dimension_id") else False
                            }
                            
                            items_to_transport.append((0, 0, courier_items))
                            
                        vals["courier_line_ids"] = items_to_transport
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Courier Service Product Not Found!"
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
            items_to_transport = []            
            search_param_values = ["", None, []]
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:
                courier_details = dict()                
                
                courier = self.env['courier.custom'].search(
                    [
                        ('id','=', int(courier_id)), '|', 
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if courier:
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
                        user = self.env['res.users'].search(
                            [
                                ('id','=', int(assigned_user_id))
                            ]
                        )                    
                        
                        if user:
                            courier_details["user_id"] = user.id
                        else:
                            response_data["code"] = 404
                            response_data["message"] = "User Not Found!"
                            return response_data

                    if priority_id not in search_param_values:
                        priority = self.env['courier.priority.custom'].search(
                            [
                                ('id','=', int(priority_id))
                            ]
                        )                    
                        
                        if priority:
                            courier_details["priority_id"] = priority.id
                        else:
                            response_data["code"] = 404
                            response_data["message"] = "Priority Not Found!"
                            return response_data                
                    
                    if category_id not in search_param_values:
                        category = self.env['courier.category.custom'].search(
                            [
                                ('id','=', int(category_id))
                            ]
                        )                    
                        
                        if category:
                            courier_details["category_id"] = category.id
                        else:
                            response_data["code"] = 404
                            response_data["message"] = "Category Not Found!"
                            return response_data                                          
                    
                    if receiver_partner_id not in search_param_values:
                        receiver = self.env['res.partner'].search(
                            [
                                ('id','=', int(receiver_partner_id))
                            ]
                        )                    
                        
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
                        sender = self.env['res.partner'].search(
                            [
                                ('id','=', int(sender_partner_id))
                            ]
                        )
                    
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
                        tags = self.env['courier.tag.custom'].search(
                            [
                                ('id','in', tag_ids)
                            ]
                        )                   
                        
                        if tags:
                            courier_details["tag_ids"] = [tag.id for tag in tags]
                        else:
                            response_data["code"] = 404
                            response_data["message"] = "Tag Not Found!"
                            return response_data
                        
                    if line_items not in search_param_values:                            
                        for item in line_items:
                            courier_items = dict()
                            
                            if item.get("product_id") not in search_param_values:
                                courier_items["product_id"] = int(item.get("product_id"))
                            if item.get("name") not in search_param_values:
                                courier_items["name"] = item.get("name")
                            if item.get("quantity") not in search_param_values:
                                courier_items["qty"] = int(item.get("quantity"))
                            if item.get("weight") not in search_param_values:
                                courier_items["weight"] = float(item.get("weight"))
                            if item.get("dimension_id") not in search_param_values:
                                courier_items["box_id"] = int(item.get("dimension_id"))
                            
                            # Check if there are any values to be updated in the line items
                            if courier_items:
                                items_to_transport.append((1, int(item.get("id")), courier_items))
                            
                        if items_to_transport:
                            courier_details["courier_line_ids"] = items_to_transport
                        
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
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except TypeError as e:
            logger.error(f"Datatype error ocurred while modifying the courier details:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while modifying the courier details:\n\n{str(e)}")
            raise e         