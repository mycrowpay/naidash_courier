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
    # _inherit = "courier.custom"
    
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