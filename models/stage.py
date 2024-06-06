import logging

from datetime import datetime
from odoo import models, _
from odoo.http import request
from odoo.exceptions import ValidationError, UserError


logger = logging.getLogger(__name__)


class NaidashCourierStage(models.Model):
    _inherit = "courier.stage.custom"
    _order = "stage_sequence asc"

    def create_stage(self, request_data):
        """Create the stage
        """ 
                
        try:
            data = dict()
            response_data = dict()
            courier_manager_group = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if courier_manager_group:            
                stage_name = request_data.get("stage_name")
                stage_sequence = int(request_data.get("stage_sequence"))
                is_form_readonly = request_data.get("is_form_readonly", False)
                allow_sales_order_creation = request_data.get("allow_sales_order_creation", False)
                
                vals = {
                    "name": stage_name,
                    "stage_sequence": stage_sequence,
                    "is_form_readonly": is_form_readonly,
                    "is_saleorder": allow_sales_order_creation
                }

                stage = self.env['courier.stage.custom'].create(vals)

                if stage:
                    data['id'] = stage.id
                    response_data["status_code"] = 201                
                    response_data["message"] = "Stage created successfully"
                    response_data["data"] = data
            else:
                response_data["status_code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"An error ocurred while creating the new stage:\n\n{str(e)}")
            raise e
        
    def edit_stage_details(self, stage_id, request_data):
        """Edit the stage details
        """ 
                
        try:
            response_data = dict()
            courier_manager_group = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if courier_manager_group:
                stage = self.env['courier.stage.custom'].search(
                    [
                        ('id','=', int(stage_id)), '|', 
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if stage:            
                    stage_name = (request_data.get("stage_name")).strip() or stage.name
                    stage_sequence = request_data.get("stage_sequence") or stage.stage_sequence
                    is_form_readonly = request_data.get("is_form_readonly") or stage.is_form_readonly
                    allow_sales_order_creation = request_data.get("allow_sales_order_creation") or stage.is_saleorder
                    fold_stage = request_data.get("fold_stage") or stage.fold
                    activate_stage = request_data.get("activate_stage") or stage.active                
                    
                    stage_details = dict(
                        name=stage_name,
                        stage_sequence=int(stage_sequence),
                        is_form_readonly=is_form_readonly,
                        is_saleorder=allow_sales_order_creation,
                        fold=fold_stage,
                        active=activate_stage
                    )
                        
                    if stage_details:
                        stage.update(stage_details)
                        response_data["status_code"] = 204                
                        response_data["message"] = "Stage updated successfully"
                else:
                    response_data["status_code"] = 404               
                    response_data["message"] = "Stage Not Found!"                    
            else:
                response_data["status_code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"An error ocurred while modifying the stage:\n\n{str(e)}")
            raise e
        
    def get_stage_details(self, stage_id):
        """Get the stage details
        """        
        
        try:
            data = dict()            
            response_data = dict()
            courier_manager_group = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for any stage regardless of the active status
            if courier_manager_group:
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
                    
                    response_data["status_code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = data
                else:
                    response_data["status_code"] = 404
                    response_data["message"] = "Stage Not Found!"
            else: 
                # Other users will access active only
                active_stage = self.env['courier.stage.custom'].search([('id','=', int(stage_id))])
                
                if active_stage:
                    data["id"] = active_stage.id
                    data["stage_name"] = active_stage.name
                    data["stage_sequence"] = active_stage.stage_sequence
                    data["is_form_readonly"] = active_stage.is_form_readonly
                    data["allow_sales_order_creation"] = active_stage.is_saleorder
                    data["fold_stage"] = active_stage.fold
                    data["activate_stage"] = active_stage.active
                    
                    response_data["status_code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = data
                else:
                    response_data["status_code"] = 404
                    response_data["message"] = "Stage Not Found!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the stage details:\n\n{str(e)}")
            raise e