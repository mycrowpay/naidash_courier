import logging

from datetime import datetime
from odoo import models, _, fields, api
from odoo.http import request
from odoo.exceptions import ValidationError, UserError


logger = logging.getLogger(__name__)


class NaidashStage(models.Model):
    _inherit = "courier.stage.custom"
    _order = "stage_sequence asc"
    
    is_last_stage = fields.Boolean(
        string = "Is This The Last Stage?",
        default = False,
        help="If set to true, this stage will be considered as the last/final step in the pipeline"
    )
    
    is_cancel_stage = fields.Boolean(
        string = "Is This The Cancellation Stage?",
        default = False,
        help="If set to true, this stage will be considered as the cancellation step in the pipeline"
    )
    
    template_id = fields.Many2one('wk.sms.template', string="Template")
    
    notification_type = fields.Selection(
        [
            ('none', 'None'),
            ('sms','SMS'),
            ('email','Email'),
            ('both','SMS & Email')
        ],
        string = "Notification Type", default="none"
    )
    
    person_to_notify = fields.Selection(
        [
            ('none', 'None'),
            ('sender','Sender'),
            ('receiver','Receiver'),
            ('both','Sender & Receiver')
        ],
        string = "Person To Notify", default="none"
    )

    def create_stage(self, request_data):
        """Create the stage
        """ 
                
        try:
            data = dict()
            response_data = dict()
            logged_in_user = self.env.user
            first_name = (logged_in_user.name).partition(" ")[0]
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:            
                stage_name = request_data.get("stage_name")
                stage_sequence = int(request_data.get("stage_sequence"))
                is_form_readonly = request_data.get("is_form_readonly", False)
                allow_sales_order_creation = request_data.get("allow_sales_order_creation", False)
                is_last_stage = request_data.get("is_last_stage", False)
                is_cancel_stage = request_data.get("is_cancel_stage", False)
                template_id = request_data.get("template_id")
                notification_type = request_data.get("notification_type")
                person_to_notify = request_data.get("person_to_notify")
                
                vals = {
                    "name": stage_name,
                    "stage_sequence": stage_sequence,
                    "is_form_readonly": is_form_readonly,
                    "is_saleorder": allow_sales_order_creation,
                    "is_last_stage": is_last_stage,
                    "is_cancel_stage": is_cancel_stage,
                    "template_id": int(template_id) if template_id else False,
                    "notification_type": notification_type,
                    "person_to_notify": person_to_notify
                }

                stage = self.env['courier.stage.custom'].create(vals)

                if stage:
                    data['id'] = stage.id
                    response_data["code"] = 201                
                    response_data["message"] = "Stage created successfully"
                    response_data["data"] = data
            else:
                response_data["code"] = 403               
                response_data["message"] = f"{first_name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"An error ocurred while creating the new stage:\n\n{str(e)}")
            raise e
        
    def edit_stage_details(self, stage_id, request_data):
        """Edit the stage details
        """ 
                
        try:
            response_data = dict()
            logged_in_user = self.env.user
            first_name = (logged_in_user.name).partition(" ")[0]
            search_param_values = ["", None]
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:
                stage = self.env['courier.stage.custom'].search(
                    [
                        ('id','=', int(stage_id)), '|', 
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if stage:
                    stage_details = dict()
                                
                    if request_data.get("stage_name") not in search_param_values:
                        stage_details["name"] = (request_data.get("stage_name")).strip()

                    if request_data.get("stage_sequence") not in search_param_values:
                        stage_details["stage_sequence"] = int(request_data.get("stage_sequence")) 
                        
                    if request_data.get("is_form_readonly") not in search_param_values:
                        stage_details["is_form_readonly"] = request_data.get("is_form_readonly")                    
                    
                    if request_data.get("allow_sales_order_creation") not in search_param_values:
                        stage_details["is_saleorder"] = request_data.get("allow_sales_order_creation")                    
                    
                    if request_data.get("fold_stage") not in search_param_values:
                        stage_details["fold"] = request_data.get("fold_stage")

                    if request_data.get("activate_stage") not in search_param_values:
                        stage_details["active"] = request_data.get("activate_stage")
                        
                    if request_data.get("is_last_stage") not in search_param_values:
                        stage_details["is_last_stage"] = request_data.get("is_last_stage")
                        
                    if request_data.get("is_cancel_stage") not in search_param_values:
                        stage_details["is_cancel_stage"] = request_data.get("is_cancel_stage")
                    
                    if request_data.get("template_id") not in search_param_values:
                        stage_details["template_id"] = int(request_data.get("template_id"))
                    
                    if request_data.get("notification_type") not in search_param_values:
                        stage_details["notification_type"] = request_data.get("notification_type")
                        
                    if request_data.get("person_to_notify") not in search_param_values:
                        stage_details["person_to_notify"] = request_data.get("person_to_notify")
                        
                    # Update stage details
                    if stage_details:
                        stage.write(stage_details)
                        response_data["code"] = 200                
                        response_data["message"] = "Stage updated successfully"
                    else:
                        response_data["code"] = 204                
                        response_data["message"] = "Nothing to update"                        
                else:
                    response_data["code"] = 404               
                    response_data["message"] = "Stage Not Found!"                    
            else:
                response_data["code"] = 403               
                response_data["message"] = f"{first_name}, You are not authorized to perform this action!"
            
            return response_data        
        except TypeError as e:
            logger.error(f"Datatype error ocurred while modifying the stage:\n\n{str(e)}")
            raise e        
        except Exception as e:
            logger.error(f"An error ocurred while modifying the stage:\n\n{str(e)}")
            raise e
        
    def get_a_stage(self, stage_id):
        """Get the stage details
        """        
        
        try:
            data = dict()            
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for 
            # any stage regardless of the active status
            if is_courier_manager:
                stage = self.env['courier.stage.custom'].search(
                    [
                        ('id','=', int(stage_id)), '|', 
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if stage:
                    data["id"] = stage.id
                    data["stage_name"] = stage.name
                    data["stage_sequence"] = stage.stage_sequence
                    data["is_form_readonly"] = stage.is_form_readonly
                    data["allow_sales_order_creation"] = stage.is_saleorder
                    data["fold_stage"] = stage.fold
                    data["activate_stage"] = stage.active
                    data["is_last_stage"] = stage.is_last_stage
                    data["is_cancel_stage"] = stage.is_cancel_stage
                    data["notification_type"] = stage.notification_type
                    data["person_to_notify"] = stage.person_to_notify
                    data["template"] = {"id": stage.template_id.id, "name": stage.template_id.name} if stage.template_id else {}
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = data
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Stage Not Found!"
            else: 
                # Other users will access active stages only
                active_stage = self.env['courier.stage.custom'].browse(int(stage_id))
                
                if active_stage:
                    data["id"] = active_stage.id
                    data["stage_name"] = active_stage.name
                    data["stage_sequence"] = active_stage.stage_sequence
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = data
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Stage Not Found!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the stage details:\n\n{str(e)}")
            raise e
        
    def get_all_stages(self, query_params):
        """Get all the stages
        """        
        
        try:
            response_data = dict()
            all_stages = []
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for 
            # any stage regardless of the active status
            if is_courier_manager:
                stages = self.env['courier.stage.custom'].search(query_params, order='stage_sequence asc')
                
                if stages:
                    for stage in stages:
                        data = dict()                    
                        data["id"] = stage.id
                        data["stage_name"] = stage.name
                        data["stage_sequence"] = stage.stage_sequence
                        data["is_form_readonly"] = stage.is_form_readonly
                        data["allow_sales_order_creation"] = stage.is_saleorder
                        data["fold_stage"] = stage.fold
                        data["activate_stage"] = stage.active
                        data["is_last_stage"] = stage.is_last_stage
                        data["is_cancel_stage"] = stage.is_cancel_stage
                        data["notification_type"] = stage.notification_type
                        data["person_to_notify"] = stage.person_to_notify
                        data["template"] = {"id": stage.template_id.id, "name": stage.template_id.name} if stage.template_id else {}
                        
                        all_stages.append(data)
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = all_stages
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Stage Not Found!"
            else: 
                # Other users will access active stages only
                all_active_stages = self.env['courier.stage.custom'].search([], order='stage_sequence asc')
                
                if all_active_stages:
                    for active_stage in all_active_stages:
                        data = dict()
                        data["id"] = active_stage.id
                        data["stage_name"] = active_stage.name
                        data["stage_sequence"] = active_stage.stage_sequence
                        
                        all_stages.append(data)
                        
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = all_stages
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Stage Not Found!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the stages:\n\n{str(e)}")
            raise e