import logging
import requests

from datetime import datetime
from odoo import models, _, fields, api
from odoo.http import request, SessionExpiredException
from odoo.exceptions import ValidationError, UserError

logger = logging.getLogger(__name__)

class NaidashProduct(models.Model):
    _inherit = "product.product"
    
    def create_the_product(self, request_data):
        """Create a product
        """ 
        
        try:
            data = dict()
            response_data = dict()
                        
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:
                product_name = request_data.get("name")
                product_code = request_data.get("code")
                price = request_data.get("price")
                can_be_sold = request_data.get("can_be_sold")
                invoice_policy = request_data.get("invoice_policy")
                product_category_id = request_data.get("category_id")
                company_id = request_data.get("company_id")
                uom_id = request_data.get("uom_id")
                tax_ids = request_data.get("tax_ids")
                product_type = request_data.get("type")
                tracking = request_data.get("tracking")

                vals = {
                    "detailed_type": product_type,
                    "tracking": tracking,
                    "expense_policy": "no"
                }
                
                if not product_name:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `product_name` parameter"
                    return response_data

                if not product_code:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `code` parameter"
                    return response_data
                
                if not product_type:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the product type"
                    return response_data                
                
                if can_be_sold == True and not price:
                    response_data["code"] = 400
                    response_data["message"] = f"Bad Request! Expected the `price` parameter if you'll be selling the {product_name}"
                    return response_data
                
                if not product_category_id:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `category_id` parameter"
                    return response_data
                
                if not invoice_policy:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `invoice_policy` parameter"
                    return response_data
                
                if not uom_id:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Expected the `uom_id` parameter"
                    return response_data                

                if price:
                    vals["lst_price"] = price
                    
                if can_be_sold == True or can_be_sold == False:
                    vals["sale_ok"] = can_be_sold
                    vals["purchase_ok"] = False
                    
                vals["name"] = product_name
                vals["default_code"] = product_code
                vals["invoice_policy"] = invoice_policy
                vals["categ_id"] = int(product_category_id)
                vals["uom_id"] = int(uom_id)
                vals["company_id"] = int(company_id) if company_id else self.env.user.company_id.id
                
                if tax_ids:
                    taxes = self.env['account.tax'].browse(tax_ids)
                    
                    if taxes:
                        vals["taxes_id"] = [tax.id for tax in taxes]
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Tax Not Found!"
                        return response_data                

                product = self.env['product.product'].create(vals)

                if product:
                    data['id'] = product.id
                    response_data["code"] = 201
                    response_data["message"] = "Created successfully"
                    response_data["data"] = data
            else:
                response_data["code"] = 403
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"An error ocurred while creating the product:\n\n{str(e)}")
            raise e
        
    def edit_the_product(self, product_id, request_data):
        """Edit the product details
        """ 
                
        try:
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:
                product = self.env['product.product'].search(
                    [
                        ('id','=', int(product_id)), '|', 
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if product:
                    product_details = dict()
                    
                    if request_data.get("tracking"):
                        product_details["tracking"] = request_data.get("tracking")
                    
                    if request_data.get("type"):
                        product_details["detailed_type"] = request_data.get("type")
                                
                    if request_data.get("name"):
                        product_details["name"] = request_data.get("name")
                        
                    if request_data.get("code"):
                        product_details["default_code"] = request_data.get("code")
                        
                    if request_data.get("price"):
                        product_details["lst_price"] = request_data.get("price")
                        
                    if request_data.get("invoice_policy"):
                        product_details["invoice_policy"] = request_data.get("invoice_policy")
                        
                    if request_data.get("category_id"):
                        product_details["categ_id"] = int(request_data.get("category_id"))

                    if request_data.get("can_be_sold"):
                        product_details["sale_ok"] = request_data.get("can_be_sold")
                        
                    if request_data.get("company_id"):
                        product_details["company_id"] = int(request_data.get("company_id"))
                        
                    if request_data.get("uom_id"):
                        product_details["uom_id"] = int(request_data.get("uom_id"))
                        
                    if request_data.get("active") == True or request_data.get("active") == False:
                        product_details["active"] = request_data.get("active")
                                            
                    if request_data.get("tax_ids"):
                        tax_ids = request_data.get("tax_ids")                        
                        taxes = self.env['account.tax'].browse(tax_ids)
                        
                        if taxes:
                            product_details["taxes_id"] = [tax.id for tax in taxes]
                        else:
                            response_data["code"] = 404
                            response_data["message"] = "Tax Not Found!"
                            return response_data                        
                        
                    # Update product details
                    if product_details:
                        product.write(product_details)
                        response_data["code"] = 200
                        response_data["message"] = "Updated successfully"
                    else:
                        response_data["code"] = 204
                        response_data["message"] = "Nothing to update"
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Product Not Found!"                    
            else:
                response_data["code"] = 403
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except TypeError as e:
            logger.error(f"Datatype error ocurred while modifying the product:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while modifying the product:\n\n{str(e)}")
            raise e
        
    def get_the_product(self, product_id):
        """Get the product details
        """        
        
        try:
            data = dict()
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for any product
            if is_courier_manager:
                product = self.env['product.product'].search(
                    [
                        ('id','=', int(product_id)), '|',
                        ('active','=', True), ('active','=', False)
                    ]
                )
                
                if product:
                    data["id"] = product.id
                    data["name"] = product.name
                    data["code"] = product.default_code or ""
                    data["type"] = product.detailed_type
                    data["can_be_sold"] = product.sale_ok
                    data["price"] = product.lst_price
                    data["invoice_policy"] = product.invoice_policy
                    data["expense_policy"] = product.expense_policy
                    data["tracking"] = product.tracking
                    data["active"] = product.active
                    data["category"] = {"id": product.categ_id.id, "name": product.categ_id.name} if product.categ_id else {}
                    data["uom"] = {"id": product.uom_id.id, "name": product.uom_id.name} if product.uom_id else {}
                    data["tax_ids"] = [{"id": tax.id, "name": tax.name} for tax in product.taxes_id] if product.taxes_id else []
                    data["company"] = {"id": product.company_id.id, "name": product.company_id.name} if product.company_id else {}
                                        
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = data
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Product Not Found!"
            else: 
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the product details:\n\n{str(e)}")
            raise e
        
    def get_all_the_products(self, query_params):
        """Get all the products
        """        
        
        try:
            response_data = dict()
            all_products = []
            search_criteria = list()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            # Courier Admins/Managers can search for products
            if is_courier_manager:
                if query_params.get("type"):
                    search_criteria.append(
                        ('detailed_type','=', query_params.get("type"))
                    )
                    
                if query_params.get("active") == True or query_params.get("active") == False:
                    search_criteria.append(
                        ('active','=', query_params.get("active"))
                    )
                                                                      
                products = self.env['product.product'].search(search_criteria)
                
                if products:
                    for product in products:
                        data = dict()
                        data["id"] = product.id
                        data["name"] = product.name
                        data["code"] = product.default_code
                        data["type"] = product.detailed_type
                        data["can_be_sold"] = product.sale_ok
                        data["price"] = product.lst_price
                        data["invoice_policy"] = product.invoice_policy
                        data["expense_policy"] = product.expense_policy
                        data["tracking"] = product.tracking
                        data["active"] = product.active
                        data["category"] = {"id": product.categ_id.id, "name": product.categ_id.name} if product.categ_id else {}
                        data["uom"] = {"id": product.uom_id.id, "name": product.uom_id.name} if product.uom_id else {}
                        data["tax_ids"] = [{"id": tax.id, "name": tax.name} for tax in product.taxes_id] if product.taxes_id else []
                        data["company"] = {"id": product.company_id.id, "name": product.company_id.name} if product.company_id else {}
                        
                        all_products.append(data)
                    
                    response_data["code"] = 200
                    response_data["message"] = "Success"
                    response_data["data"] = all_products
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Product Not Found!"
            else: 
                response_data["code"] = 403
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the products:\n\n{str(e)}")
            raise e