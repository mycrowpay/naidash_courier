import logging
import requests

from datetime import datetime
from odoo import models, _, fields, api
from odoo.http import request, SessionExpiredException
from odoo.exceptions import ValidationError, UserError

logger = logging.getLogger(__name__)

class NaidashTax(models.Model):
    _inherit = "account.tax"
    
    def create_the_tax(self, request_data):
        """Create a tax
        """ 
        
        try:
            data = dict()
            response_data = dict()
            invoice_repartition_lines = []
            refund_repartition_lines = []
                        
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:
                name = request_data.get("name")
                description = request_data.get("description")
                amount = request_data.get("amount")
                country_id = request_data.get("country_id")
                tax_group_id = request_data.get("tax_group_id")
                invoice_repartition_line_items = request_data.get("invoice_repartition_line_items")
                refund_repartition_line_items = request_data.get("refund_repartition_line_items")
                
                vals = {
                    "tax_scope": "service",
                    "type_tax_use": "sale",
                    "amount_type": "percent",
                    "invoice_label": description
                }
                
                if not name:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `name` parameter"
                    return response_data

                if not description:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `description` parameter"
                    return response_data
                
                if not amount:
                    response_data["code"] = 400
                    response_data["message"] = f"Bad Request! Expected the `amount` parameter"
                    return response_data
                
                if not country_id:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `country_id` parameter"
                    return response_data
                
                if not tax_group_id:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `tax_group_id` parameter"
                    return response_data
                
                if not invoice_repartition_line_items:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `invoice_repartition_line_items` parameter"
                    return response_data
                
                if isinstance(invoice_repartition_line_items, list) == False:
                    response_data["code"] = 422
                    response_data["message"] = "Unprocessable Content! Expected a list of objects in `invoice_repartition_line_items` parameter"
                    return response_data
                
                if not refund_repartition_line_items:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `refund_repartition_line_items` parameter"
                    return response_data
                
                if isinstance(refund_repartition_line_items, list) == False:
                    response_data["code"] = 422
                    response_data["message"] = "Unprocessable Content! Expected a list of objects in `refund_repartition_line_items` parameter"
                    return response_data                                
                
                vals["name"] = name
                vals["description"] = description
                vals["amount"] = amount
                vals["country_id"] = int(country_id)
                vals["tax_group_id"] = int(tax_group_id)
                                    
                if invoice_repartition_line_items:
                    for item in invoice_repartition_line_items:
                        repartition_line = {
                            "factor_percent": item.get("percentage_factor"),
                            "repartition_type": item.get("repartition_type"),
                            "account_id": int(item.get("account_id")) if item.get("account_id") else False
                        }
                        
                        invoice_repartition_lines.append((0, 0, repartition_line))
                        
                    vals["invoice_repartition_line_ids"] = invoice_repartition_lines
                    
                if refund_repartition_line_items:
                    for item in refund_repartition_line_items:
                        repartition_line = {
                            "factor_percent": item.get("percentage_factor"),
                            "repartition_type": item.get("repartition_type"),
                            "account_id": int(item.get("account_id")) if item.get("account_id") else False
                        }
                        
                        refund_repartition_lines.append((0, 0, repartition_line))
                        
                    vals["refund_repartition_line_ids"] = refund_repartition_lines

                tax = self.env['account.tax'].create(vals)

                if tax:
                    data['id'] = tax.id
                    response_data["code"] = 201
                    response_data["message"] = "Created successfully"
                    response_data["data"] = data
            else:
                response_data["code"] = 403
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except TypeError as e:
            logger.error(f"Datatype error ocurred while creating the tax:\n\n{str(e)}")
            raise e        
        except Exception as e:
            logger.error(f"An error ocurred while creating the tax:\n\n{str(e)}")
            raise e
        
    def edit_the_tax(self, tax_id, request_data):
        """Edit the tax details
        """ 
                
        try:
            response_data = dict()
            invoice_repartition_lines = []
            refund_repartition_lines = []
            search_param_values = ["", None, []]
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:
                tax = self.env['account.tax'].search(
                    [
                        ('id','=', int(tax_id)), ('tax_scope','=', 'service'), 
                        '|', ('active','=', True), ('active','=', False)
                    ]
                )
                
                if tax:
                    tax_details = dict()
                    name = request_data.get("name")
                    description = request_data.get("description")
                    amount = request_data.get("amount")                    
                    country_id = request_data.get("country_id")
                    tax_group_id = request_data.get("tax_group_id")
                    is_record_active = request_data.get("active")
                    invoice_repartition_line_items = request_data.get("invoice_repartition_line_items")
                    refund_repartition_line_items = request_data.get("refund_repartition_line_items")
                                                
                    if name:
                        tax_details["name"] = name
                        
                    if description:
                        tax_details["invoice_label"] = description
                        tax_details["description"] = description
                        
                    if amount:
                        tax_details["amount"] = amount
                        
                    if country_id:
                        tax_details["country_id"] = int(country_id)
                        
                    if tax_group_id:
                        tax_details["tax_group_id"] = int(tax_group_id)                        
                        
                    if is_record_active == True or is_record_active == False:
                        tax_details["active"] = is_record_active

                    if invoice_repartition_line_items not in search_param_values:
                        for item in invoice_repartition_line_items:
                            repartition_line = dict()
                            
                            if item.get("percentage_factor") not in search_param_values:
                                repartition_line["factor_percent"] = item.get("percentage_factor")
                            if item.get("repartition_type") not in search_param_values:
                                repartition_line["repartition_type"] = item.get("repartition_type")
                            if item.get("account_id") not in search_param_values:
                                repartition_line["account_id"] = int(item.get("account_id"))
                            
                            # Check if there are any values to be updated in the line items
                            if repartition_line:
                                invoice_repartition_lines.append((1, int(item.get("id")), repartition_line))
                            
                        if invoice_repartition_lines:
                            tax_details["invoice_repartition_line_ids"] = invoice_repartition_lines
                            
                    if refund_repartition_line_items not in search_param_values:
                        for item in refund_repartition_line_items:
                            repartition_line = dict()
                            
                            if item.get("percentage_factor") not in search_param_values:
                                repartition_line["factor_percent"] = item.get("percentage_factor")
                            if item.get("repartition_type") not in search_param_values:
                                repartition_line["repartition_type"] = item.get("repartition_type")
                            if item.get("account_id") not in search_param_values:
                                repartition_line["account_id"] = int(item.get("account_id"))
                            
                            # Check if there are any values to be updated in the line items
                            if repartition_line:
                                refund_repartition_lines.append((1, int(item.get("id")), repartition_line))
                            
                        if refund_repartition_lines:
                            tax_details["refund_repartition_line_ids"] = refund_repartition_lines
                        
                    # Update tax details
                    if tax_details:
                        tax.write(tax_details)
                        response_data["code"] = 200
                        response_data["message"] = "Updated successfully"
                    else:
                        response_data["code"] = 204
                        response_data["message"] = "Nothing to update"
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Tax Not Found!"                    
            else:
                response_data["code"] = 403
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except TypeError as e:
            logger.error(f"Datatype error ocurred while modifying the tax:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while modifying the tax:\n\n{str(e)}")
            raise e
        
    def get_the_tax(self, tax_id):
        """Get the tax details
        """        
        
        try:
            data = dict()
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for 
            # any tax regardless of the active status
            if is_courier_manager:
                tax = self.env['account.tax'].search(
                    [
                        ('id','=', int(tax_id)), ('tax_scope','=', 'service'), 
                        '|', ('active','=', True), ('active','=', False)
                    ]
                )
                
                if tax:
                    data["id"] = tax.id
                    data["name"] = tax.name
                    data["description"] = tax.description or ""
                    data["invoice_label"] = tax.invoice_label or ""
                    data["amount"] = tax.amount
                    data["tax_scope"] = tax.tax_scope
                    data["tax_type"] = tax.type_tax_use
                    data["tax_computation"] = tax.amount_type
                    data["active"] = tax.active
                    data["tax_group"] = {"id": tax.tax_group_id.id, "name": tax.tax_group_id.name} if tax.tax_group_id else {}
                    data["company"] = {"id": tax.company_id.id, "name": tax.company_id.name} if tax.company_id else {}
                    data["country"] = {"id": tax.country_id.id, "name": tax.country_id.name} if tax.country_id else {}
                    data["invoice_repartition_line_items"] = [
                        {
                            "id": item.id,
                            "percentage_factor": item.factor_percent,
                            "repartition_type": item.repartition_type,
                            "account": {"id": item.account_id.id, "name": item.account_id.name} if item.account_id else {}
                        } for item in tax.invoice_repartition_line_ids
                    ] if tax.invoice_repartition_line_ids else []
                    
                    data["refund_repartition_line_items"] = [
                        {
                            "id": item.id,
                            "percentage_factor": item.factor_percent,
                            "repartition_type": item.repartition_type,
                            "account": {"id": item.account_id.id, "name": item.account_id.name} if item.account_id else {}
                        } for item in tax.refund_repartition_line_ids
                    ] if tax.refund_repartition_line_ids else []
                                        
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = data
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Tax Not Found!"
            else: 
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the tax details:\n\n{str(e)}")
            raise e
        
    def get_all_the_taxes(self):
        """Get all the taxes
        """        
        
        try:
            response_data = dict()
            all_taxes = []
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for 
            # any taxes regardless of the active status
            if is_courier_manager:
                taxes = self.env['account.tax'].search(
                    [
                        ('tax_scope','=', 'service'),
                        '|',
                        ('active','=', True),
                        ('active','=', False)
                    ])
                
                if taxes:
                    for tax in taxes:
                        data = dict()
                        data["id"] = tax.id
                        data["name"] = tax.name
                        data["description"] = tax.description or ""
                        data["invoice_label"] = tax.invoice_label or ""
                        data["amount"] = tax.amount
                        data["tax_scope"] = tax.tax_scope
                        data["tax_type"] = tax.type_tax_use
                        data["tax_computation"] = tax.amount_type
                        data["active"] = tax.active
                        data["tax_group"] = {"id": tax.tax_group_id.id, "name": tax.tax_group_id.name} if tax.tax_group_id else {}
                        data["company"] = {"id": tax.company_id.id, "name": tax.company_id.name} if tax.company_id else {}
                        data["country"] = {"id": tax.country_id.id, "name": tax.country_id.name} if tax.country_id else {}
                        data["invoice_repartition_line_items"] = [
                            {
                                "id": item.id,
                                "percentage_factor": item.factor_percent,
                                "repartition_type": item.repartition_type,
                                "account": {"id": item.account_id.id, "name": item.account_id.name} if item.account_id else {}
                            } for item in tax.invoice_repartition_line_ids
                        ] if tax.invoice_repartition_line_ids else []
                        
                        data["refund_repartition_line_items"] = [
                            {
                                "id": item.id,
                                "percentage_factor": item.factor_percent,
                                "repartition_type": item.repartition_type,
                                "account": {"id": item.account_id.id, "name": item.account_id.name} if item.account_id else {}
                            } for item in tax.refund_repartition_line_ids
                        ] if tax.refund_repartition_line_ids else []
                        
                        all_taxes.append(data)
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = all_taxes
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Tax Not Found!"
            else: 
                response_data["code"] = 403
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the taxes:\n\n{str(e)}")
            raise e