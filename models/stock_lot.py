import logging
import requests

from datetime import datetime
from odoo import models, _, fields, api
from odoo.http import request, SessionExpiredException
from odoo.exceptions import ValidationError, UserError

logger = logging.getLogger(__name__)

class NaidashStockLot(models.Model):
    _inherit = "stock.lot"
    
    def create_the_stock_lot(self, request_data):
        """Create a stock_lot
        """ 
        
        try:
            data = dict()
            response_data = dict()
                        
            lot_or_serial_number = request_data.get("lot_or_serial_no")
            product_id = request_data.get("product_id")
            internal_reference_no = request_data.get("internal_reference_no","")
            description = request_data.get("description","")
            
            if not lot_or_serial_number:
                response_data["code"] = 400
                response_data["message"] = "Bad Request! Expected a unique lot or serial number"
                return response_data

            if not product_id:
                response_data["code"] = 400
                response_data["message"] = "Bad Request! Expected the product id"
                return response_data
            
            product = self.env['product.product'].search(
                [
                    ('id', '=', int(product_id)),
                    ('detailed_type', '=', 'product'), 
                    ('tracking', '!=', 'none')
                ]
            )
            
            if product:
                vals = dict()
                vals["name"] = lot_or_serial_number
                vals["product_id"] = product.id
                vals["note"] = description
                vals["ref"] = internal_reference_no
                vals["company_id"] = product.company_id.id if product.company_id else self.env.user.company_id.id
                
                stock_lot = self.env['stock.lot'].create(vals)
                
                if stock_lot:
                    data['id'] = stock_lot.id
                    response_data["code"] = 201
                    response_data["message"] = "Created successfully"
                    response_data["data"] = data
                else:
                    response_data["code"] = 204
                    response_data["message"] = "Could not create the stock lot"
                    return response_data
            else:
                response_data["code"] = 404
                response_data["message"] = "Product not found!"
                return response_data
            
            return response_data
        except Exception as e:
            logger.error(f"An error ocurred while creating the stock lot:\n\n{str(e)}")
            raise e
        
    def edit_the_stock_lot(self, stock_lot_id, request_data):
        """Edit the stock lot details
        """ 
                
        try:
            response_data = dict()
            logged_in_user = self.env.user
            
            stock_lot = self.env['stock.lot'].search(
                [
                    ("id", "=", int(stock_lot_id)),
                    ("company_id", "=", logged_in_user.company_id.id)
                ]
            )
            
            if stock_lot:
                stock_lot_details = dict()
                
                if request_data.get("lot_or_serial_no"):
                    stock_lot_details["name"] = request_data.get("lot_or_serial_no")
                
                if request_data.get("product_id"):
                    stock_lot_details["product_id"] = int(request_data.get("product_id"))
                            
                if request_data.get("internal_reference_no"):
                    stock_lot_details["ref"] = request_data.get("internal_reference_no")
                    
                if request_data.get("description"):
                    stock_lot_details["note"] = request_data.get("description")
                    
                if request_data.get("stock_location_id"):
                    stock_lot_details["location_id"] = int(request_data.get("stock_location_id"))
                    
                # Update stock lot details
                if stock_lot_details:
                    stock_lot.write(stock_lot_details)
                    response_data["code"] = 200
                    response_data["message"] = "Updated successfully"
                else:
                    response_data["code"] = 204
                    response_data["message"] = "Nothing to update"
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock lot not found!"                    
            
            return response_data
        except TypeError as e:
            logger.error(f"Datatype error ocurred while modifying the stock lot:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while modifying the stock lot:\n\n{str(e)}")
            raise e
        
    def get_the_stock_lot(self, stock_lot_id):
        """Get the stock lot details
        """        
        
        try:
            data = dict()
            response_data = dict()
            logged_in_user = self.env.user
            
            stock_lot = self.env['stock.lot'].search(
                [
                    ("id", "=", int(stock_lot_id)),
                    ("company_id", "=", logged_in_user.company_id.id)
                ]
            )            
            
            if stock_lot:
                data["id"] = stock_lot.id
                data["lot_or_serial_no"] = stock_lot.name
                data["internal_reference_no"] = stock_lot.ref or ""
                data["description"] = stock_lot.note or ""
                data["quantity"] = stock_lot.product_qty
                data["product"] = {"id": stock_lot.product_id.id, "name": stock_lot.product_id.name} if stock_lot.product_id else {}
                data["stock_location"] = {"id": stock_lot.location_id.id, "name": stock_lot.location_id.name} if stock_lot.location_id else {}
                data["company"] = {"id": stock_lot.company_id.id, "name": stock_lot.company_id.name} if stock_lot.company_id else {}
                                    
                response_data["code"] = 200
                response_data["message"] = "Success"
                response_data["data"] = data
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock lot not found!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the stock lot details:\n\n{str(e)}")
            raise e
        
    def get_all_the_stock_lots(self):
        """Get all the stock lots
        """        
        
        try:
            response_data = dict()
            all_stock_lots = []
            logged_in_user = self.env.user
            search_criteria = [("company_id", "=", logged_in_user.company_id.id)]
            
            stock_lots = self.env['stock.lot'].search(search_criteria)
            
            if stock_lots:
                for stock_lot in stock_lots:
                    data = dict()
                    data["id"] = stock_lot.id
                    data["lot_or_serial_no"] = stock_lot.name
                    data["internal_reference_no"] = stock_lot.ref or ""
                    data["description"] = stock_lot.note or ""
                    data["quantity"] = stock_lot.product_qty
                    data["product"] = {"id": stock_lot.product_id.id, "name": stock_lot.product_id.name} if stock_lot.product_id else {}
                    data["stock_location"] = {"id": stock_lot.location_id.id, "name": stock_lot.location_id.name} if stock_lot.location_id else {}
                    data["company"] = {"id": stock_lot.company_id.id, "name": stock_lot.company_id.name} if stock_lot.company_id else {}
                    
                    all_stock_lots.append(data)
                
                response_data["code"] = 200
                response_data["message"] = "Success"
                response_data["data"] = all_stock_lots
            else:
                response_data["code"] = 404
                response_data["message"] = "Stock lot not found!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the stock lots:\n\n{str(e)}")
            raise e