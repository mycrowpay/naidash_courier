import logging
import pytz
import base64
import re

from datetime import datetime, date, timedelta
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.http import request,content_disposition
from odoo.exceptions import ValidationError, UserError, AccessError, AccessDenied, MissingError

from .utils import NaidashUtils

logger = logging.getLogger(__name__)
nautils = NaidashUtils()

class NaidashInvoice(models.Model):
    _inherit = 'account.move'    
    
    def create_invoice_from_sales_order(self, request_data):
        """Create Invoice from Sales Order
        """
        
        try:
            data = dict()
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:
                sale_id = request_data.get("sale_id")
                
                if not sale_id:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `sale_id` request parameter"
                    return response_data
                
                sales_order = self.env['sale.order'].search(
                    [
                        ('id','=', int(sale_id))
                    ]
                )
                
                if sales_order:
                    # Create Invoice
                    invoice = sales_order._create_invoices()    
                    
                    if invoice:
                        data['id'] = invoice.id
                        response_data["code"] = 201
                        response_data["message"] = "Invoice created successfully"
                        response_data["data"] = data
                        
                    courier_stage_update = sales_order.custom_courier_id.move_to_next_stage(sales_order.custom_courier_id.id)
                    status_code = courier_stage_update.get("code")
                    if status_code == 200:                                     
                        response_data["message"] = response_data["message"] + ".Kindly `confirm` or `cancel` the invoice"                    
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Sales order not found!"
            else:
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"                        
            return response_data
        except AccessError as e:
            logger.error(f"Access error ocurred while creating the invoice:\n\n{str(e)}")
            raise e
        except TypeError as e:
            logger.error(f"Datatype error ocurred while creating the invoice:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while creating the invoice:\n\n{str(e)}")
            raise e
        
    def get_an_invoice(self, invoice_id):
        """Get the invoice details
        """        
        
        try:
            data = dict()            
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search 
            # for more details in an invoice
            if is_courier_manager:
                invoice = self.env['account.move'].search(
                    [
                        ('id','=', int(invoice_id))
                    ]
                )
                
                if invoice:
                    data["id"] = invoice.id
                    data["name"] = invoice.name
                    data["stage"] = invoice.state
                    data["payment_reference"] = invoice.payment_reference or ""
                    data["invoice_date"] = (invoice.invoice_date).strftime("%Y-%m-%d") if invoice.invoice_date else ""
                    data["invoice_due_date"] = (invoice.invoice_date_due).strftime("%Y-%m-%d") if invoice.invoice_date_due else ""
                    data["order_reference"] = invoice.ref
                    data["origin"] = invoice.invoice_origin
                    data["auto_post"] = invoice.auto_post
                    
                    # Use the creator's local timezone
                    user_timezone = invoice.create_uid.tz or pytz.utc
                    user_timezone = pytz.timezone(user_timezone)
                        
                    creation_date = (invoice.create_date).strftime("%Y-%m-%d %H:%M")
                    creation_date = datetime.strftime(
                        pytz.utc.localize(datetime.strptime(creation_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                        "%Y-%m-%d %H:%M"
                    )
                    
                    data["created_date"] = creation_date
                    data["created_by"] = invoice.create_uid.name
                    data["subtotal"] = invoice.amount_untaxed
                    data["tax_amount"] = invoice.amount_tax
                    data["total_amount"] = invoice.amount_total
                    data["amount_paid"] = invoice.amount_paid
                    data["amount_due"] = invoice.amount_residual
                    data["currency"] = {"id": invoice.currency_id.id, "name": invoice.currency_id.name} if invoice.currency_id else {}
                    data["courier"] = {"id": invoice.custom_courier_id.id, "name": invoice.custom_courier_id.name} if invoice.custom_courier_id else {}
                    data["sales_person"] = {"id": invoice.invoice_user_id.id, "name": invoice.invoice_user_id.name} if invoice.invoice_user_id else {}
                    data["company"] = {"id": invoice.company_id.id, "name": invoice.company_id.name} if invoice.company_id else {}
                    data["journal"] = {"id": invoice.journal_id.id, "name": invoice.journal_id.name} if invoice.journal_id else {}
                    data["payment_terms"] = {"id": invoice.invoice_payment_term_id.id, "name": invoice.invoice_payment_term_id.name} if invoice.invoice_payment_term_id else {}                    
                                        
                    data["partner"] = {
                        "id": invoice.partner_id.id,
                        "name": invoice.partner_id.name,
                        "phone": invoice.partner_id.phone,
                        "email": invoice.partner_id.email,
                        "country": {"id": invoice.partner_id.country_id.id, "name": invoice.partner_id.country_id.name} if invoice.partner_id.country_id else {},
                        "state": {"id": invoice.partner_id.state_id.id, "name": invoice.partner_id.state_id.name} if invoice.partner_id.state_id else {},
                        "address": invoice.partner_id.street
                    } if invoice.partner_id else {}
                    
                    data["invoice_line_items"] = [
                        {
                            "id": item.id, 
                            "item_no": item.sequence,
                            "description": item.name,
                            "quantity": item.quantity,
                            "unit_price": item.price_unit,
                            "subtotal": item.price_subtotal,
                            "total": item.price_total,
                            "tax": [{"id": tax.id, "name": tax.name} for tax in item.tax_ids] if item.tax_ids else [],
                            "product": {"id": item.product_id.id, "name": item.product_id.name} if item.product_id else {},
                            "currency": {"id": item.currency_id.id, "name": item.currency_id.name} if item.currency_id else {},
                            "account": {"id": item.account_id.id, "name": item.account_id.name} if item.account_id else {}
                        } for item in invoice.invoice_line_ids
                    ] if invoice.invoice_line_ids else []
                    
                    data["journal_line_items"] = [
                        {
                            "id": item.id,
                            "description": item.name,
                            "debit": item.debit,
                            "credit": item.credit,
                            "discount": item.discount_amount_currency,                            
                            "currency": {"id": item.currency_id.id, "name": item.currency_id.name} if item.currency_id else {},
                            "account": {"id": item.account_id.id, "name": item.account_id.name} if item.account_id else {}
                        } for item in invoice.line_ids
                    ] if invoice.line_ids else []                    
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = data
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Invoice not found!"
            else:
                active_invoice = self.env['account.move'].search(
                    [
                        ('id', '=', int(invoice_id))
                    ]
                )
                
                if active_invoice:
                    data["id"] = active_invoice.id
                    data["name"] = active_invoice.name
                    data["stage"] = active_invoice.state
                    data["payment_reference"] = active_invoice.payment_reference or ""
                    data["invoice_date"] = (active_invoice.invoice_date).strftime("%Y-%m-%d") if active_invoice.invoice_date else ""
                    data["invoice_due_date"] = (active_invoice.invoice_date_due).strftime("%Y-%m-%d") if active_invoice.invoice_date_due else ""
                    data["order_reference"] = active_invoice.ref
                    data["origin"] = active_invoice.invoice_origin
                    data["auto_post"] = active_invoice.auto_post
                    
                    # Use the creator's local timezone
                    user_timezone = active_invoice.create_uid.tz or pytz.utc
                    user_timezone = pytz.timezone(user_timezone)
                        
                    creation_date = (active_invoice.create_date).strftime("%Y-%m-%d %H:%M")
                    creation_date = datetime.strftime(
                        pytz.utc.localize(datetime.strptime(creation_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                        "%Y-%m-%d %H:%M"
                    )
                    
                    data["created_date"] = creation_date
                    data["created_by"] = active_invoice.create_uid.name
                    data["subtotal"] = active_invoice.amount_untaxed
                    data["tax_amount"] = active_invoice.amount_tax
                    data["total_amount"] = active_invoice.amount_total
                    data["amount_paid"] = active_invoice.amount_paid
                    data["amount_due"] = active_invoice.amount_residual
                    data["currency"] = {"id": active_invoice.currency_id.id, "name": active_invoice.currency_id.name} if active_invoice.currency_id else {}
                    data["courier"] = {"id": active_invoice.custom_courier_id.id, "name": active_invoice.custom_courier_id.name} if active_invoice.custom_courier_id else {}
                    data["sales_person"] = {"id": active_invoice.invoice_user_id.id, "name": active_invoice.invoice_user_id.name} if active_invoice.invoice_user_id else {}
                    data["company"] = {"id": active_invoice.company_id.id, "name": active_invoice.company_id.name} if active_invoice.company_id else {}
                    data["journal"] = {"id": active_invoice.journal_id.id, "name": active_invoice.journal_id.name} if active_invoice.journal_id else {}
                    data["payment_terms"] = {"id": active_invoice.invoice_payment_term_id.id, "name": active_invoice.invoice_payment_term_id.name} if active_invoice.invoice_payment_term_id else {}                    
                                        
                    data["partner"] = {
                        "id": active_invoice.partner_id.id, 
                        "name": active_invoice.partner_id.name,
                        "phone": active_invoice.partner_id.phone,
                        "email": active_invoice.partner_id.email,
                        "country": {"id": active_invoice.partner_id.country_id.id, "name": active_invoice.partner_id.country_id.name} if active_invoice.partner_id.country_id else {},
                        "state": {"id": active_invoice.partner_id.state_id.id, "name": active_invoice.partner_id.state_id.name} if active_invoice.partner_id.state_id else {},
                        "address": active_invoice.partner_id.street
                    } if active_invoice.partner_id else {}
                    
                    data["invoice_line_items"] = [
                        {
                            "id": item.id, 
                            "item_no": item.sequence,
                            "description": item.name,
                            "quantity": item.quantity,
                            "unit_price": item.price_unit,
                            "subtotal": item.price_subtotal,
                            "total": item.price_total,
                            "tax": [{"id": tax.id, "name": tax.name} for tax in item.tax_ids] if item.tax_ids else [],
                            "product": {"id": item.product_id.id, "name": item.product_id.name} if item.product_id else {},
                            "currency": {"id": item.currency_id.id, "name": item.currency_id.name} if item.currency_id else {},
                            "account": {"id": item.account_id.id, "name": item.account_id.name} if item.account_id else {}
                        } for item in active_invoice.invoice_line_ids
                    ] if active_invoice.invoice_line_ids else []
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = data
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Invoice not found!"
                                
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the invoice details:\n\n{str(e)}")
            raise e
        
    def get_all_invoices(self, query_params):
        """Get all invoices based
        on the query parameters
        """        
        
        try:
            response_data = dict()
            search_criteria = list()
            all_invoices = []
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            logged_in_user = self.env.user
            user_timezone = logged_in_user.tz or pytz.utc
            user_timezone = pytz.timezone(user_timezone)            
            
            if query_params.get("partner_id"):
                search_criteria.append(
                    ('partner_id','=', query_params.get("partner_id"))
                )
                
            if query_params.get("stage"):
                search_criteria.append(
                    ('state','=', query_params.get("stage"))
                )                
                
            if query_params.get("due_date_from") and query_params.get("due_date_to"):
                due_date_from = query_params.get("due_date_from")
                due_date_to = query_params.get("due_date_to")
                
                search_criteria.append(
                    ('invoice_date_due','>=',(datetime(due_date_from.year, due_date_from.month, due_date_from.day)).strftime('%Y-%m-%d 00:00:00'))
                )
                
                search_criteria.append(
                    ('invoice_date_due','<=',(datetime(due_date_to.year, due_date_to.month, due_date_to.day)).strftime('%Y-%m-%d 23:59:59'))
                )
                                                                                                                                                            
            # Courier Admins/Managers can search 
            # for more details on invoices
            if is_courier_manager:
                if query_params.get("created_date_from") and query_params.get("created_date_to"):
                    created_date_from = query_params.get("created_date_from")
                    created_date_to = query_params.get("created_date_to")
                    
                    search_criteria.append(
                        ('create_date','>=',(datetime(created_date_from.year, created_date_from.month, created_date_from.day)).strftime('%Y-%m-%d 00:00:00'))
                    )
                    
                    search_criteria.append(
                        ('create_date','<=',(datetime(created_date_to.year, created_date_to.month, created_date_to.day)).strftime('%Y-%m-%d 23:59:59'))
                    )                    
                                                   
                invoices = self.env['account.move'].search(search_criteria, order='id desc')
                
                if invoices:
                    for invoice in invoices:
                        data = dict()                    
                        data["id"] = invoice.id
                        data["name"] = invoice.name
                        data["stage"] = invoice.state
                        data["payment_reference"] = invoice.payment_reference or ""
                        data["invoice_date"] = (invoice.invoice_date).strftime("%Y-%m-%d") if invoice.invoice_date else ""
                        data["invoice_due_date"] = (invoice.invoice_date_due).strftime("%Y-%m-%d") if invoice.invoice_date_due else ""
                        data["order_reference"] = invoice.ref
                        data["origin"] = invoice.invoice_origin
                        data["auto_post"] = invoice.auto_post
                            
                        creation_date = (invoice.create_date).strftime("%Y-%m-%d %H:%M")
                        creation_date = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(creation_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["created_date"] = creation_date
                        data["created_by"] = invoice.create_uid.name
                        data["subtotal"] = invoice.amount_untaxed
                        data["tax_amount"] = invoice.amount_tax
                        data["total_amount"] = invoice.amount_total
                        data["amount_paid"] = invoice.amount_paid
                        data["amount_due"] = invoice.amount_residual
                        data["currency"] = {"id": invoice.currency_id.id, "name": invoice.currency_id.name} if invoice.currency_id else {}
                        data["courier"] = {"id": invoice.custom_courier_id.id, "name": invoice.custom_courier_id.name} if invoice.custom_courier_id else {}
                        data["sales_person"] = {"id": invoice.invoice_user_id.id, "name": invoice.invoice_user_id.name} if invoice.invoice_user_id else {}
                        data["company"] = {"id": invoice.company_id.id, "name": invoice.company_id.name} if invoice.company_id else {}
                        data["journal"] = {"id": invoice.journal_id.id, "name": invoice.journal_id.name} if invoice.journal_id else {}
                        data["payment_terms"] = {"id": invoice.invoice_payment_term_id.id, "name": invoice.invoice_payment_term_id.name} if invoice.invoice_payment_term_id else {}                    
                                            
                        data["partner"] = {
                            "id": invoice.partner_id.id,
                            "name": invoice.partner_id.name,
                            "phone": invoice.partner_id.phone,
                            "email": invoice.partner_id.email,
                            "country": {"id": invoice.partner_id.country_id.id, "name": invoice.partner_id.country_id.name} if invoice.partner_id.country_id else {},
                            "state": {"id": invoice.partner_id.state_id.id, "name": invoice.partner_id.state_id.name} if invoice.partner_id.state_id else {},
                            "address": invoice.partner_id.street
                        } if invoice.partner_id else {}
                        
                        data["invoice_line_items"] = [
                            {
                                "id": item.id, 
                                "item_no": item.sequence,
                                "description": item.name,
                                "quantity": item.quantity,
                                "unit_price": item.price_unit,
                                "subtotal": item.price_subtotal,
                                "total": item.price_total,
                                "tax": [{"id": tax.id, "name": tax.name} for tax in item.tax_ids] if item.tax_ids else [],
                                "product": {"id": item.product_id.id, "name": item.product_id.name} if item.product_id else {},
                                "currency": {"id": item.currency_id.id, "name": item.currency_id.name} if item.currency_id else {},
                                "account": {"id": item.account_id.id, "name": item.account_id.name} if item.account_id else {}
                            } for item in invoice.invoice_line_ids
                        ] if invoice.invoice_line_ids else []
                        
                        data["journal_line_items"] = [
                            {
                                "id": item.id,
                                "description": item.name,
                                "debit": item.debit,
                                "credit": item.credit,
                                "discount": item.discount_amount_currency,                            
                                "currency": {"id": item.currency_id.id, "name": item.currency_id.name} if item.currency_id else {},
                                "account": {"id": item.account_id.id, "name": item.account_id.name} if item.account_id else {}
                            } for item in invoice.line_ids
                        ] if invoice.line_ids else []
                        
                        all_invoices.append(data)
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = all_invoices
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Invoice not found!"
            else:
                active_invoices = self.env['account.move'].search(search_criteria, order='id asc')
                
                if active_invoices:
                    for active_invoice in active_invoices:
                        data = dict()
                        data["id"] = active_invoice.id
                        data["name"] = active_invoice.name
                        data["stage"] = active_invoice.state
                        data["payment_reference"] = active_invoice.payment_reference or ""
                        data["invoice_date"] = (active_invoice.invoice_date).strftime("%Y-%m-%d") if active_invoice.invoice_date else ""
                        data["invoice_due_date"] = (active_invoice.invoice_date_due).strftime("%Y-%m-%d") if active_invoice.invoice_date_due else ""
                        data["order_reference"] = active_invoice.ref
                        data["origin"] = active_invoice.invoice_origin
                        data["auto_post"] = active_invoice.auto_post
                            
                        creation_date = (active_invoice.create_date).strftime("%Y-%m-%d %H:%M")
                        creation_date = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(creation_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["created_date"] = creation_date
                        data["created_by"] = active_invoice.create_uid.name
                        data["subtotal"] = active_invoice.amount_untaxed
                        data["tax_amount"] = active_invoice.amount_tax
                        data["total_amount"] = active_invoice.amount_total
                        data["amount_paid"] = active_invoice.amount_paid
                        data["amount_due"] = active_invoice.amount_residual
                        data["currency"] = {"id": active_invoice.currency_id.id, "name": active_invoice.currency_id.name} if active_invoice.currency_id else {}
                        data["courier"] = {"id": active_invoice.custom_courier_id.id, "name": active_invoice.custom_courier_id.name} if active_invoice.custom_courier_id else {}
                        data["sales_person"] = {"id": active_invoice.invoice_user_id.id, "name": active_invoice.invoice_user_id.name} if active_invoice.invoice_user_id else {}
                        data["company"] = {"id": active_invoice.company_id.id, "name": active_invoice.company_id.name} if active_invoice.company_id else {}
                        data["journal"] = {"id": active_invoice.journal_id.id, "name": active_invoice.journal_id.name} if active_invoice.journal_id else {}
                        data["payment_terms"] = {"id": active_invoice.invoice_payment_term_id.id, "name": active_invoice.invoice_payment_term_id.name} if active_invoice.invoice_payment_term_id else {}                    
                                            
                        data["partner"] = {
                            "id": active_invoice.partner_id.id, 
                            "name": active_invoice.partner_id.name,
                            "phone": active_invoice.partner_id.phone,
                            "email": active_invoice.partner_id.email,
                            "country": {"id": active_invoice.partner_id.country_id.id, "name": active_invoice.partner_id.country_id.name} if active_invoice.partner_id.country_id else {},
                            "state": {"id": active_invoice.partner_id.state_id.id, "name": active_invoice.partner_id.state_id.name} if active_invoice.partner_id.state_id else {},
                            "address": active_invoice.partner_id.street
                        } if active_invoice.partner_id else {}
                        
                        data["invoice_line_items"] = [
                            {
                                "id": item.id, 
                                "item_no": item.sequence,
                                "description": item.name,
                                "quantity": item.quantity,
                                "unit_price": item.price_unit,
                                "subtotal": item.price_subtotal,
                                "total": item.price_total,
                                "tax": [{"id": tax.id, "name": tax.name} for tax in item.tax_ids] if item.tax_ids else [],
                                "product": {"id": item.product_id.id, "name": item.product_id.name} if item.product_id else {},
                                "currency": {"id": item.currency_id.id, "name": item.currency_id.name} if item.currency_id else {},
                                "account": {"id": item.account_id.id, "name": item.account_id.name} if item.account_id else {}
                            } for item in active_invoice.invoice_line_ids
                        ] if active_invoice.invoice_line_ids else []
                                            
                        all_invoices.append(data)
                        
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = all_invoices
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Invoice not found!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the invoices:\n\n{str(e)}")
            raise e
        
    def confirm_the_sales_order_invoice(self, invoice_id):
        """ Confirm the invoice
        """
        
        try:
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can confirm an invoice
            if is_courier_manager:
                invoice = self.env['account.move'].search(
                    [
                        ('id','=', int(invoice_id))
                    ]
                )
                
                if invoice:
                    invoice.action_post()
                    response_data["code"] = 200
                    response_data["message"] = "Invoice confirmed"
                
                    courier_stage_update = self.env['courier.custom'].move_to_next_stage(invoice.custom_courier_id.id)
                    status_code = courier_stage_update.get("code")

                    if status_code == 200:
                        response_data["message"] = response_data["message"] + " successfully"
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Invoice not found!"
            else:
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, This action is forbidden!"
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while confirming the invoice details:\n\n{str(e)}")
            raise e
        
    def cancel_the_sales_order_invoice(self, invoice_id):
        """ Cancel the invoice
        """
        
        try:
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can cancel an invoice
            if is_courier_manager:
                invoice = self.env['account.move'].search(
                    [
                        ('id','=', int(invoice_id))
                    ]
                )
                
                if invoice:
                    invoice.button_cancel()
                    response_data["code"] = 200
                    response_data["message"] = "Invoice cancelled successfully"
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Invoice not found!"
            else:
                response_data["code"] = 403
                response_data["message"] = f"{self.env.user.name}, This action is forbidden!"
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while cancelling the invoice:\n\n{str(e)}")
            raise e
        
    def reset_the_sales_order_invoice_to_draft(self, invoice_id):
        """ Reset a posted/cancelled invoice to draft
        """
        
        try:
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can reset an invoice to draft
            if is_courier_manager:
                invoice = self.env['account.move'].search(
                    [
                        ('id','=', int(invoice_id))
                    ]
                )
                
                if invoice:
                    invoice.button_draft()
                    response_data["code"] = 200
                    response_data["message"] = "Invoice successfully set to draft"
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Invoice not found!"
            else:
                response_data["code"] = 403
                response_data["message"] = f"{self.env.user.name}, This action is forbidden!"
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while resetting the invoice to draft:\n\n{str(e)}")
            raise e
        
    def download_the_sales_order_invoice(self, invoice_id):
        """ Download a PDF version of the invoice
        """
        
        try:
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search
            # and download posted invoices
            if is_courier_manager:
                invoice = self.env['account.move'].search(
                    [
                        ('id','=', int(invoice_id)),
                        ('state','=', 'posted')
                    ]
                )
                
                if invoice:
                    attached_invoice = ""
                    
                    # Send & Print wizard with only the 'download' checkbox to get the official attachment(s)
                    template = self.env.ref(invoice._get_mail_template())
                    attachment_ids = invoice._generate_pdf_and_send_invoice(template, bypass_download=True, checkbox_send_mail=False, checkbox_download=True)
                    attachments = self.env['ir.attachment'].browse(attachment_ids)
                    if len(attachments) > 1:
                        filename = invoice._get_invoice_report_filename(extension='zip')
                        zip_content = attachments.sudo()._build_zip_from_attachments()
                        headers = nautils.get_zip_headers(zip_content, filename)
                        return request.make_response(zip_content, headers)
                    
                    headers = nautils.get_http_headers(invoice, "pdf", attachments.raw, True)

                    # Check for the attached invoice
                    if attachments and attachments.raw:
                        attached_invoice = attachments.raw
                                            
                        response_data["code"] = 200
                        response_data["headers"] = list(headers.items())
                        response_data["message"] = "Downloaded successfully"
                        response_data["data"] = attached_invoice
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Document not found"
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Only posted invoices can be downloaded!"
            else:
                response_data["code"] = 403
                response_data["message"] = f"{self.env.user.name}, This action is forbidden!"
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while downloading the invoice:\n\n{str(e)}")
            raise e