import logging
import pytz

from datetime import datetime, date, timedelta
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.http import request
from odoo.exceptions import ValidationError, UserError
from .utils import NaidashUtils

logger = logging.getLogger(__name__)
nautils = NaidashUtils()

class NaidashSaleOrder(models.Model):
    _inherit = 'sale.order'
    
    def create_sale_order(self, request_data):
        """Create Sale Order
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
                        
                        if sale_order:
                            data['id'] = sale_order.id
                            response_data["code"] = 201
                            response_data["message"] = "Sales order created successfully"
                            response_data["data"] = data
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
        
    def get_a_sale_order(self, sale_id):
        """Get the sale order details
        """        
        
        try:
            data = dict()            
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search 
            # for more details in a sale order
            if is_courier_manager:
                sale_order = self.env['sale.order'].search(
                    [
                        ('id','=', int(sale_id))
                    ]
                )
                
                if sale_order:
                    data["id"] = sale_order.id
                    data["name"] = sale_order.name
                    data["picking_policy"] = sale_order.picking_policy
                    data["origin"] = sale_order.origin
                    data["order_reference"] = sale_order.client_order_ref
                    data["delivery_status"] = sale_order.delivery_status or ""
                    data["quotation_expiry_date"] = (sale_order.validity_date).strftime("%Y-%m-%d") if sale_order.validity_date else ""
                    data["quotation_date"] = ""
                    data["delivery_date"] = ""
                    
                    # Display the delivery time using the assigned user's local timezone
                    assigned_user_timezone = sale_order.user_id.tz or pytz.utc
                    assigned_user_timezone = pytz.timezone(assigned_user_timezone)
                    
                    if sale_order.commitment_date:
                        delivery_date = (sale_order.commitment_date).strftime("%Y-%m-%d %H:%M")
                        delivery_date = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(delivery_date, "%Y-%m-%d %H:%M")).astimezone(assigned_user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["delivery_date"] = delivery_date
                        
                    if sale_order.date_order:
                        quotation_date = (sale_order.date_order).strftime("%Y-%m-%d %H:%M")
                        quotation_date = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(quotation_date, "%Y-%m-%d %H:%M")).astimezone(assigned_user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["quotation_date"] = quotation_date
                    
                    data["subtotal"] = sale_order.amount_untaxed
                    data["tax_amount"] = sale_order.amount_tax
                    data["total_amount"] = sale_order.amount_total
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
                            "unit_price": item.price_unit,
                            "subtotal": item.price_subtotal,                            
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
                    response_data["message"] = "Sale Order Not Found!"
            else:
                active_sale_order = self.env['sale.order'].search(
                    [
                        ('id', '=', int(sale_id))
                    ]
                )
                
                if active_sale_order:
                    data["id"] = active_sale_order.id
                    data["name"] = active_sale_order.name
                    data["picking_policy"] = active_sale_order.picking_policy
                    data["origin"] = active_sale_order.origin
                    data["order_reference"] = active_sale_order.client_order_ref
                    data["delivery_status"] = active_sale_order.delivery_status or ""
                    data["quotation_expiry_date"] = (active_sale_order.validity_date).strftime("%Y-%m-%d") if active_sale_order.validity_date else ""
                    data["quotation_date"] = ""
                    data["delivery_date"] = ""
                    
                    # Display the delivery time using the assigned user's local timezone
                    assigned_user_timezone = active_sale_order.user_id.tz or pytz.utc
                    assigned_user_timezone = pytz.timezone(assigned_user_timezone)
                    
                    if active_sale_order.commitment_date:
                        delivery_date = (active_sale_order.commitment_date).strftime("%Y-%m-%d %H:%M")
                        delivery_date = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(delivery_date, "%Y-%m-%d %H:%M")).astimezone(assigned_user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["delivery_date"] = delivery_date
                        
                    if active_sale_order.date_order:
                        quotation_date = (active_sale_order.date_order).strftime("%Y-%m-%d %H:%M")
                        quotation_date = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(quotation_date, "%Y-%m-%d %H:%M")).astimezone(assigned_user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["quotation_date"] = quotation_date
                                            
                    data["subtotal"] = sale_order.amount_untaxed
                    data["tax_amount"] = sale_order.amount_tax
                    data["total_amount"] = sale_order.amount_total                   
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
                            "unit_price": item.price_unit,
                            "subtotal": item.price_subtotal,                            
                        } for item in active_sale_order.order_line
                    ] if active_sale_order.order_line else []
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = data
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Sale Order Not Found!"
                                
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the sale order details:\n\n{str(e)}")
            raise e        