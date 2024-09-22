import logging
import pytz

from datetime import datetime, date, timedelta
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.http import request
from odoo.exceptions import ValidationError, UserError, AccessError, AccessDenied
from .utils import NaidashUtils

logger = logging.getLogger(__name__)
nautils = NaidashUtils()

class NaidashSalesOrder(models.Model):
    _inherit = 'sale.order'
    
    def create_sales_order(self, request_data):
        """Create a sales order
        """
        
        try:
            vals = dict()
            data = dict()
            response_data = dict()
            sales_order_lines = [] 
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:
                courier_id = request_data.get("courier_id")
                
                if not courier_id:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `courier_id` request parameter"
                    return response_data
                
                courier = self.env['courier.custom'].search(
                    [
                        ('id','=', int(courier_id))
                    ]
                )
                
                if courier:
                    if courier.courier_line_ids and courier.stage_id.is_saleorder:
                        vals["custom_courier_id"] = courier.id
                        vals["partner_id"] = courier.receiver_name_id.id if courier.is_receiver_invoice else courier.sender_name_id.id
                        vals["origin"] = courier.name
                        vals["commitment_date"] = courier.delivery_date
                        vals["delivery_status"] = "pending"
                        vals["client_order_ref"] = nautils.generate_payment_token()
                        # vals["picking_policy"] = "direct"
                        # vals["invoice_status"] = "to invoice"
                        # vals["payment_term_id"] = "The payment terms"
                        # vals["user_id"] = "The Salesperson"
                        # vals["company_id"] = "The Salesperson's Company"
                        # vals["analytic_account_id"] = "The Analytic Account"
                        # vals["journal_id"] = "The Invoicing Journal"
                        # vals["reference"] = "The payment reference for this sales order"
                        # vals["require_payment"] = "Online Payment"
                        # vals["require_signature"] = "Online signature"

                        for item in courier.courier_line_ids:
                            if item.weight_cost > item.volumetric_weight_cost:
                                price_cost = item.weight_cost
                                name = '%s | %s | %s kg' % (item.product_id.name,item.name,item.weight)
                            elif item.volumetric_weight_cost > item.weight_cost:
                                price_cost = item.volumetric_weight_cost
                                name = '%s | %s | %s cm' % (item.product_id.name,item.name,item.box_id.name)
                            elif item.weight_cost == item.volumetric_weight_cost:
                                price_cost = item.weight_cost
                                name = '%s | %s | %s kg' % (item.product_id.name,item.name,item.weight)
                            
                            courier_items = {
                                "courier_line_id": item.id,
                                "product_id": item.product_id.id,
                                "name": name,
                                "product_uom_qty": item.qty,
                                "price_unit": price_cost,
                            }
                            
                            sales_order_lines.append((0, 0, courier_items))
                            
                        if courier.distance_product_id:
                            if courier.distance:
                                name = '%s | %s km' % (courier.distance_product_id.name, str(courier.distance))
                            else:
                                name = '%s' % (courier.distance_product_id.name)
                            distance_charges_product = courier._create_charges_line(courier.distance_product_id, name, courier.distance_charges)
                            sales_order_lines.append(distance_charges_product)
                        
                        if courier.additional_product_id:
                            if courier.priority_id:
                                name = '%s | %s' % (courier.additional_product_id.name,courier.priority_id.name)
                            else:
                                name = '%s' % (courier.additional_product_id.name)  
                            additional_charges_product = courier._create_charges_line(courier.additional_product_id, name, courier.additional_charges)
                            sales_order_lines.append(additional_charges_product)
                        
                        # Add sales order line items
                        vals["order_line"] = sales_order_lines
                        
                        # Create Sales Order
                        sale_order = self.env['sale.order'].create(vals)
                        
                        # Update the Courier Request 
                        courier.write({"sale_order_id": sale_order.id})

                        if sale_order:
                            data['id'] = sale_order.id
                            response_data["code"] = 201
                            response_data["message"] = "Sale order created successfully"
                            response_data["data"] = data
                            
                        courier_stage_update = courier.move_to_next_stage(courier.id)
                        status_code = courier_stage_update.get("code")
                        if status_code == 200:                                     
                            response_data["code"] = 201
                            response_data["message"] = "Sale order created & courier request " + courier_stage_update.get("message")
                        else:
                            return courier_stage_update                        
                    else:
                        response_data["code"] = 400
                        response_data["message"] = f"Bad request! Detected an invalid stage or no line items in {courier.name}"
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
            logger.error(f"Datatype error ocurred while creating the sale order:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while creating the sale order:\n\n{str(e)}")
            raise e
        
    def get_a_sales_order(self, sale_id):
        """Get the sales order details
        """
        
        try:
            data = dict()            
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            logged_in_user = self.env.user
            user_timezone = logged_in_user.tz or pytz.utc
            user_timezone = pytz.timezone(user_timezone)
                        
            # Courier Admins/Managers can search 
            # for more details in a sales order
            if is_courier_manager:
                sale_order = self.env['sale.order'].search(
                    [
                        ('id','=', int(sale_id))
                    ]
                )
                
                if sale_order:
                    data["id"] = sale_order.id
                    data["name"] = sale_order.name
                    data["stage"] = sale_order.state
                    data["picking_policy"] = sale_order.picking_policy
                    data["origin"] = sale_order.origin
                    data["order_reference"] = sale_order.client_order_ref
                    data["delivery_status"] = sale_order.delivery_status or ""
                    data["quotation_expiry_date"] = (sale_order.validity_date).strftime("%Y-%m-%d") if sale_order.validity_date else ""
                    data["quotation_date"] = ""
                    data["delivery_date"] = ""
                    
                    if sale_order.commitment_date:
                        delivery_date = (sale_order.commitment_date).strftime("%Y-%m-%d %H:%M")
                        delivery_date = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(delivery_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["delivery_date"] = delivery_date
                        
                    if sale_order.date_order:
                        quotation_date = (sale_order.date_order).strftime("%Y-%m-%d %H:%M")
                        quotation_date = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(quotation_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["quotation_date"] = quotation_date
                        
                    creation_date = (sale_order.create_date).strftime("%Y-%m-%d %H:%M")
                    creation_date = datetime.strftime(
                        pytz.utc.localize(datetime.strptime(creation_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                        "%Y-%m-%d %H:%M"
                    )
                    
                    data["created_date"] = creation_date
                    data["created_by"] = sale_order.create_uid.name
                    data["subtotal"] = sale_order.amount_untaxed
                    data["tax_amount"] = sale_order.amount_tax
                    data["total_amount"] = sale_order.amount_total
                    data["invoicing_status"] = sale_order.invoice_status
                    data["invoice"] = [{"id": invoice.id, "name": invoice.name, "stage": invoice.state} for invoice in sale_order.invoice_ids] if sale_order.invoice_ids else []
                    data["currency"] = {"id": sale_order.currency_id.id, "name": sale_order.currency_id.name} if sale_order.currency_id else {}
                    data["analytic_account"] = {"id": sale_order.analytic_account_id.id, "name": sale_order.analytic_account_id.name} if sale_order.analytic_account_id else {}
                    data["journal"] = {"id": sale_order.journal_id.id, "name": sale_order.journal_id.name} if sale_order.journal_id else {}
                    data["courier"] = {"id": sale_order.custom_courier_id.id, "name": sale_order.custom_courier_id.name} if sale_order.custom_courier_id else {}
                    data["company"] = {"id": sale_order.company_id.id, "name": sale_order.company_id.name} if sale_order.company_id else {}
                    data["sales_person"] = {"id": sale_order.user_id.id, "name": sale_order.user_id.name} if sale_order.user_id else {}
                    data["payment_terms"] = {"id": sale_order.payment_term_id.id, "name": sale_order.payment_term_id.name} if sale_order.payment_term_id else {}                    
                                        
                    data["partner"] = {
                        "id": sale_order.partner_id.id, 
                        "name": sale_order.partner_id.name,
                        "phone": sale_order.partner_id.phone,
                        "email": sale_order.partner_id.email,
                        "country": {"id": sale_order.partner_id.country_id.id, "name": sale_order.partner_id.country_id.name} if sale_order.partner_id.country_id else {},
                        "state": {"id": sale_order.partner_id.state_id.id, "name": sale_order.partner_id.state_id.name} if sale_order.partner_id.state_id else {},
                        "address": sale_order.partner_id.street
                    } if sale_order.partner_id else {}
                    
                    data["line_items"] = [
                        {
                            "id": item.id, 
                            "description": item.name,
                            "quantity": item.product_uom_qty,
                            "invoiced_quantity": item.qty_invoiced,
                            "unit_price": item.price_unit,
                            "subtotal": item.price_subtotal,
                            "total": item.price_total,
                            "tax": {"id": item.tax_id.id, "name": item.tax_id.name} if item.tax_id else {},
                            "courier_line": {"id": item.courier_line_id.id, "name": item.courier_line_id.name} if item.courier_line_id else {},
                            "product": {"id": item.product_id.id, "name": item.product_id.name} if item.product_id else {}
                        } for item in sale_order.order_line
                    ] if sale_order.order_line else []
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = data
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Sales order not found!"
            else:
                active_sale_order = self.env['sale.order'].search(
                    [
                        ('id', '=', int(sale_id))
                    ]
                )
                
                if active_sale_order:
                    data["id"] = active_sale_order.id
                    data["name"] = active_sale_order.name
                    data["stage"] = active_sale_order.state                    
                    data["picking_policy"] = active_sale_order.picking_policy
                    data["origin"] = active_sale_order.origin
                    data["order_reference"] = active_sale_order.client_order_ref
                    data["delivery_status"] = active_sale_order.delivery_status or ""
                    data["quotation_expiry_date"] = (active_sale_order.validity_date).strftime("%Y-%m-%d") if active_sale_order.validity_date else ""
                    data["quotation_date"] = ""
                    data["delivery_date"] = ""
                    
                    if active_sale_order.commitment_date:
                        delivery_date = (active_sale_order.commitment_date).strftime("%Y-%m-%d %H:%M")
                        delivery_date = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(delivery_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["delivery_date"] = delivery_date
                        
                    if active_sale_order.date_order:
                        quotation_date = (active_sale_order.date_order).strftime("%Y-%m-%d %H:%M")
                        quotation_date = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(quotation_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["quotation_date"] = quotation_date
                                            
                    creation_date = (active_sale_order.create_date).strftime("%Y-%m-%d %H:%M")
                    creation_date = datetime.strftime(
                        pytz.utc.localize(datetime.strptime(creation_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                        "%Y-%m-%d %H:%M"
                    )
                    
                    data["created_date"] = creation_date
                    data["created_by"] = active_sale_order.create_uid.name
                    data["subtotal"] = active_sale_order.amount_untaxed
                    data["tax_amount"] = active_sale_order.amount_tax
                    data["total_amount"] = active_sale_order.amount_total
                    data["invoicing_status"] = active_sale_order.invoice_status
                    data["invoice"] = [{"id": invoice.id, "name": invoice.name, "stage": invoice.state} for invoice in active_sale_order.invoice_ids] if active_sale_order.invoice_ids else []
                    data["currency"] = {"id": active_sale_order.currency_id.id, "name": active_sale_order.currency_id.name} if active_sale_order.currency_id else {}
                    data["courier"] = {"id": active_sale_order.custom_courier_id.id, "name": active_sale_order.custom_courier_id.name} if active_sale_order.custom_courier_id else {}
                    data["sales_person"] = {"id": active_sale_order.user_id.id, "name": active_sale_order.user_id.name} if active_sale_order.user_id else {}
                    data["payment_terms"] = {"id": active_sale_order.payment_term_id.id, "name": active_sale_order.payment_term_id.name} if active_sale_order.payment_term_id else {}                    
                                        
                    data["partner"] = {
                        "id": active_sale_order.partner_id.id, 
                        "name": active_sale_order.partner_id.name,
                        "phone": active_sale_order.partner_id.phone,
                        "email": active_sale_order.partner_id.email,
                        "country": {"id": active_sale_order.partner_id.country_id.id, "name": active_sale_order.partner_id.country_id.name} if active_sale_order.partner_id.country_id else {},
                        "state": {"id": active_sale_order.partner_id.state_id.id, "name": active_sale_order.partner_id.state_id.name} if active_sale_order.partner_id.state_id else {},
                        "address": active_sale_order.partner_id.street
                    } if active_sale_order.partner_id else {}
                    
                    data["line_items"] = [
                        {
                            "id": item.id, 
                            "description": item.name,
                            "quantity": item.product_uom_qty,
                            "invoiced_quantity": item.qty_invoiced,
                            "unit_price": item.price_unit,
                            "subtotal": item.price_subtotal,
                            "total": item.price_total
                        } for item in active_sale_order.order_line
                    ] if active_sale_order.order_line else []
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = data
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Sales order not found!"
                                
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the sales order details:\n\n{str(e)}")
            raise e
        
    def get_all_sales_orders(self, query_params):
        """Get all sales orders
        based on the query parameters
        """        
        
        try:
            response_data = dict()
            search_criteria = list()
            all_sales_orders = []
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
                
            if query_params.get("quotation_date_from") and query_params.get("quotation_date_to"):
                quotation_date_from = query_params.get("quotation_date_from")
                quotation_date_to = query_params.get("quotation_date_to")
                
                search_criteria.append(
                    ('date_order','>=',(datetime(quotation_date_from.year, quotation_date_from.month, quotation_date_from.day)).strftime('%Y-%m-%d 00:00:00'))
                )
                
                search_criteria.append(
                    ('date_order','<=',(datetime(quotation_date_to.year, quotation_date_to.month, quotation_date_to.day)).strftime('%Y-%m-%d 23:59:59'))
                )                 
                
            if query_params.get("delivery_date_from") and query_params.get("delivery_date_to"):
                delivery_date_from = query_params.get("delivery_date_from")
                delivery_date_to = query_params.get("delivery_date_to")

                search_criteria.append(
                    ('commitment_date','>=',(datetime(delivery_date_from.year, delivery_date_from.month, delivery_date_from.day)).strftime('%Y-%m-%d 00:00:00'))
                )
                
                search_criteria.append(
                    ('commitment_date','<=',(datetime(delivery_date_to.year, delivery_date_to.month, delivery_date_to.day)).strftime('%Y-%m-%d 23:59:59'))                    
                )
                                                                                                                                                            
            # Courier Admins/Managers can search 
            # for more details in a sales orders
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
                                                   
                sales_orders = self.env['sale.order'].search(search_criteria, order='id desc')
                
                if sales_orders:
                    for sale_order in sales_orders:
                        data = dict()                    
                        data["id"] = sale_order.id
                        data["name"] = sale_order.name
                        data["stage"] = sale_order.state
                        data["picking_policy"] = sale_order.picking_policy
                        data["origin"] = sale_order.origin
                        data["order_reference"] = sale_order.client_order_ref
                        data["delivery_status"] = sale_order.delivery_status or ""
                        data["quotation_expiry_date"] = (sale_order.validity_date).strftime("%Y-%m-%d") if sale_order.validity_date else ""
                        data["quotation_date"] = ""
                        data["delivery_date"] = ""
                        
                        if sale_order.commitment_date:
                            delivery_date = (sale_order.commitment_date).strftime("%Y-%m-%d %H:%M")
                            delivery_date = datetime.strftime(
                                pytz.utc.localize(datetime.strptime(delivery_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                                "%Y-%m-%d %H:%M"
                            )
                            
                            data["delivery_date"] = delivery_date
                            
                        if sale_order.date_order:
                            quotation_date = (sale_order.date_order).strftime("%Y-%m-%d %H:%M")
                            quotation_date = datetime.strftime(
                                pytz.utc.localize(datetime.strptime(quotation_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                                "%Y-%m-%d %H:%M"
                            )
                            
                            data["quotation_date"] = quotation_date
                            
                        creation_date = (sale_order.create_date).strftime("%Y-%m-%d %H:%M")
                        creation_date = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(creation_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["created_date"] = creation_date
                        data["created_by"] = sale_order.create_uid.name
                        data["subtotal"] = sale_order.amount_untaxed
                        data["tax_amount"] = sale_order.amount_tax
                        data["total_amount"] = sale_order.amount_total
                        data["invoicing_status"] = sale_order.invoice_status
                        data["invoice"] = [{"id": invoice.id, "name": invoice.name, "stage": invoice.state} for invoice in sale_order.invoice_ids] if sale_order.invoice_ids else []
                        data["currency"] = {"id": sale_order.currency_id.id, "name": sale_order.currency_id.name} if sale_order.currency_id else {}
                        data["analytic_account"] = {"id": sale_order.analytic_account_id.id, "name": sale_order.analytic_account_id.name} if sale_order.analytic_account_id else {}
                        data["journal"] = {"id": sale_order.journal_id.id, "name": sale_order.journal_id.name} if sale_order.journal_id else {}
                        data["courier"] = {"id": sale_order.custom_courier_id.id, "name": sale_order.custom_courier_id.name} if sale_order.custom_courier_id else {}
                        data["company"] = {"id": sale_order.company_id.id, "name": sale_order.company_id.name} if sale_order.company_id else {}
                        data["sales_person"] = {"id": sale_order.user_id.id, "name": sale_order.user_id.name} if sale_order.user_id else {}
                        data["payment_terms"] = {"id": sale_order.payment_term_id.id, "name": sale_order.payment_term_id.name} if sale_order.payment_term_id else {}                    
                                            
                        data["partner"] = {
                            "id": sale_order.partner_id.id, 
                            "name": sale_order.partner_id.name,
                            "phone": sale_order.partner_id.phone,
                            "email": sale_order.partner_id.email,
                            "country": {"id": sale_order.partner_id.country_id.id, "name": sale_order.partner_id.country_id.name} if sale_order.partner_id.country_id else {},
                            "state": {"id": sale_order.partner_id.state_id.id, "name": sale_order.partner_id.state_id.name} if sale_order.partner_id.state_id else {},
                            "address": sale_order.partner_id.street
                        } if sale_order.partner_id else {}
                        
                        data["line_items"] = [
                            {
                                "id": item.id,
                                "description": item.name,
                                "quantity": item.product_uom_qty,
                                "invoiced_quantity": item.qty_invoiced,
                                "unit_price": item.price_unit,
                                "subtotal": item.price_subtotal,
                                "total": item.price_total,
                                "tax": {"id": item.tax_id.id, "name": item.tax_id.name} if item.tax_id else {},
                                "courier_line": {"id": item.courier_line_id.id, "name": item.courier_line_id.name} if item.courier_line_id else {},
                                "product": {"id": item.product_id.id, "name": item.product_id.name} if item.product_id else {}
                            } for item in sale_order.order_line
                        ] if sale_order.order_line else []
                        
                        all_sales_orders.append(data)
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = all_sales_orders
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Sales order not found!"
            else:
                active_sales_orders = self.env['sale.order'].search(search_criteria, order='id asc')
                
                if active_sales_orders:
                    for active_sale_order in active_sales_orders:
                        data = dict()
                        data["id"] = active_sale_order.id
                        data["name"] = active_sale_order.name
                        data["stage"] = active_sale_order.state                    
                        data["picking_policy"] = active_sale_order.picking_policy
                        data["origin"] = active_sale_order.origin
                        data["order_reference"] = active_sale_order.client_order_ref
                        data["delivery_status"] = active_sale_order.delivery_status or ""
                        data["quotation_expiry_date"] = (active_sale_order.validity_date).strftime("%Y-%m-%d") if active_sale_order.validity_date else ""
                        data["quotation_date"] = ""
                        data["delivery_date"] = ""
                        
                        if active_sale_order.commitment_date:
                            delivery_date = (active_sale_order.commitment_date).strftime("%Y-%m-%d %H:%M")
                            delivery_date = datetime.strftime(
                                pytz.utc.localize(datetime.strptime(delivery_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                                "%Y-%m-%d %H:%M"
                            )
                            
                            data["delivery_date"] = delivery_date
                            
                        if active_sale_order.date_order:
                            quotation_date = (active_sale_order.date_order).strftime("%Y-%m-%d %H:%M")
                            quotation_date = datetime.strftime(
                                pytz.utc.localize(datetime.strptime(quotation_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                                "%Y-%m-%d %H:%M"
                            )
                            
                            data["quotation_date"] = quotation_date
                                                
                        creation_date = (active_sale_order.create_date).strftime("%Y-%m-%d %H:%M")
                        creation_date = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(creation_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["created_date"] = creation_date
                        data["created_by"] = active_sale_order.create_uid.name
                        data["subtotal"] = active_sale_order.amount_untaxed
                        data["tax_amount"] = active_sale_order.amount_tax
                        data["total_amount"] = active_sale_order.amount_total
                        data["invoicing_status"] = sale_order.invoice_status
                        data["invoice"] = [{"id": invoice.id, "name": invoice.name, "stage": invoice.state} for invoice in active_sale_order.invoice_ids] if active_sale_order.invoice_ids else []
                        data["currency"] = {"id": active_sale_order.currency_id.id, "name": active_sale_order.currency_id.name} if active_sale_order.currency_id else {}
                        data["courier"] = {"id": active_sale_order.custom_courier_id.id, "name": active_sale_order.custom_courier_id.name} if active_sale_order.custom_courier_id else {}
                        data["sales_person"] = {"id": active_sale_order.user_id.id, "name": active_sale_order.user_id.name} if active_sale_order.user_id else {}
                        data["payment_terms"] = {"id": active_sale_order.payment_term_id.id, "name": active_sale_order.payment_term_id.name} if active_sale_order.payment_term_id else {}                    
                                            
                        data["partner"] = {
                            "id": active_sale_order.partner_id.id, 
                            "name": active_sale_order.partner_id.name,
                            "phone": active_sale_order.partner_id.phone,
                            "email": active_sale_order.partner_id.email,
                            "country": {"id": active_sale_order.partner_id.country_id.id, "name": active_sale_order.partner_id.country_id.name} if active_sale_order.partner_id.country_id else {},
                            "state": {"id": active_sale_order.partner_id.state_id.id, "name": active_sale_order.partner_id.state_id.name} if active_sale_order.partner_id.state_id else {},
                            "address": active_sale_order.partner_id.street
                        } if active_sale_order.partner_id else {}
                        
                        data["line_items"] = [
                            {
                                "id": item.id,
                                "description": item.name,
                                "quantity": item.product_uom_qty,
                                "invoiced_quantity": item.qty_invoiced,
                                "unit_price": item.price_unit,
                                "subtotal": item.price_subtotal,
                                "total": item.price_total
                            } for item in active_sale_order.order_line
                        ] if active_sale_order.order_line else []
                                            
                        all_sales_orders.append(data)
                        
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = all_sales_orders
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Sales Order Not Found!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the sales orders:\n\n{str(e)}")
            raise e
        
    def confirm_sales_order(self, sale_order_id):
        """ Confirm the sales order and set the confirmation date.
        """
        
        try:
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can confirm a sale order
            if is_courier_manager:
                sale_order = self.env['sale.order'].search(
                    [
                        ('id','=', int(sale_order_id))
                    ]
                )
                
                if sale_order:
                    if not all(order._can_be_confirmed() for order in sale_order):
                        response_data["code"] = 409
                        response_data["message"] = f"The following sales order can't be confirmed: {', '.join(sale_order.mapped('display_name'))}"
                        return response_data

                    sale_order.order_line._validate_analytic_distribution()

                    for order in sale_order:
                        order.validate_taxes_on_sales_order()
                        if order.partner_id in order.message_partner_ids:
                            continue
                        order.message_subscribe([order.partner_id.id])

                    confirmed_sale_order = sale_order.write(sale_order._prepare_confirmation_values())

                    if confirmed_sale_order:
                        response_data["code"] = 200
                        response_data["message"] = "Sales order confirmed"

                    # Context key 'default_name' is sometimes propagated up to here.
                    # We don't need it and it creates issues in the creation of linked records.
                    context = sale_order._context.copy()
                    context.pop('default_name', None)

                    sale_order.with_context(context)._action_confirm()

                    sale_order.filtered(lambda so: so._should_be_locked()).action_lock()
                    
                    courier_stage_update = self.env['courier.custom'].move_to_next_stage(sale_order.custom_courier_id.id)
                    status_code = courier_stage_update.get("code")
                    if status_code == 200:
                        response_data["message"] = response_data["message"] + " successfully"
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Sales order not found!"
            else:
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, This action is forbidden!"
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while confirming the sales order details:\n\n{str(e)}")
            raise e
        
    def cancel_sales_order(self, sale_order_id):
        """ Cancel the sales order
        """
        
        try:
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can cancel a sales order
            if is_courier_manager:
                sale_order = self.env['sale.order'].search(
                    [
                        ('id','=', int(sale_order_id))
                    ]
                )
                
                if sale_order:
                    if any(order.locked for order in sale_order):
                        response_data["code"] = 403
                        response_data["message"] = f"{self.env.user.name}, You cannot cancel a locked sales order.Please unlock it first"
                        return response_data
                    
                    can_be_cancelled = sale_order._show_cancel_wizard()
                    if can_be_cancelled:
                        response_data["code"] = 403
                        response_data["message"] = f"Sales order {sale_order.name} cannot be cancelled"
                    else:
                        cancelled_sales_order = sale_order._action_cancel()
                    
                        if cancelled_sales_order:
                            response_data["code"] = 200
                            response_data["message"] = f"Sales order {sale_order.name} has been cancelled"
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Sales order not found!"                            
            else:
                response_data["code"] = 403
                response_data["message"] = f"{self.env.user.name}, This action is forbidden!"
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while cancelling the sales order:\n\n{str(e)}")
            raise e