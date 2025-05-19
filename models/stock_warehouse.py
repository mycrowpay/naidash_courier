import logging
import requests
import pytz

from datetime import datetime, date, timedelta
from odoo import models, _, fields, api
from odoo.http import request, SessionExpiredException
from odoo.exceptions import ValidationError, UserError

logger = logging.getLogger(__name__)

class NaidashStockWarehouse(models.Model):
    _inherit = "stock.warehouse"
    
    def create_the_warehouse(self, request_data):
        """Create the stock warehouse
        """ 
        
        try:
            vals = dict()
            data = dict()
            response_data = dict()
                                    
            warehouse_name = request_data.get("name")
            warehouse_code = request_data.get("code")
            partner_id = request_data.get("partner_id")

            if not partner_id:
                response_data["code"] = 400
                response_data["message"] = "Bad Request! Expected the partner's id"
                return response_data

            if not warehouse_name:
                response_data["code"] = 400
                response_data["message"] = "Bad Request! Expected the warehouse name"
                return response_data
            
            if not warehouse_code:
                response_data["code"] = 400
                response_data["message"] = "Bad Request! Expected the warehouse code"
                return response_data
            
            vals["name"] = warehouse_name
            vals["code"] = warehouse_code
            
            partner = self.env['res.partner'].browse(int(partner_id))
            
            if partner:
                vals["partner_id"] = partner.id
            else:
                response_data["code"] = 404
                response_data["message"] = "Partner not found!"
                return response_data
            
            stock_picking = self.env['stock.warehouse'].create(vals)
            
            if stock_picking:
                data['id'] = stock_picking.id
                response_data["code"] = 201
                response_data["message"] = "Created successfully"
                response_data["data"] = data
            else:
                response_data["code"] = 204
                response_data["message"] = "Failed to create the warehouse"
                return response_data
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while creating the warehouse:\n\n{str(e)}")
            raise e
        
    def edit_the_warehouse(self, warehouse_id, request_data):
        """Edit the warehouse details
        """ 
                
        try:
            response_data = dict()
            logged_in_user = self.env.user
            
            warehouse = self.env['stock.warehouse'].search(
                [
                    ("id", "=", int(warehouse_id)),
                    ("company_id", "=", logged_in_user.company_id.id),
                    ("active", "in", [True, False])
                ]
            )
            
            if warehouse:
                warehouse_details = dict()
                                
                if request_data.get("name"):
                    warehouse_details["name"] = request_data.get("name")

                if request_data.get("code"):
                    warehouse_details["code"] = request_data.get("code")
                    
                if request_data.get("active") == True or request_data.get("active") == False:
                    warehouse_details["active"] = request_data.get("active")
                    
                if request_data.get("resupply_from_warehouse_ids"):
                    warehouse_details["resupply_wh_ids"] = request_data.get("resupply_from_warehouse_ids")
                                    
                if request_data.get("partner_id"):
                    partner_id = request_data.get("partner_id")
                    partner = self.env['res.partner'].browse(int(partner_id))
                    
                    if partner:
                        warehouse_details["partner_id"] = partner.id
                    else:
                        response_data["code"] = 404
                        response_data["message"] = "Partner not found!"
                        return response_data
                                        
                # Update warehouse details
                if warehouse_details:
                    warehouse.write(warehouse_details)
                    response_data["code"] = 200
                    response_data["message"] = "Updated successfully"
                else:
                    response_data["code"] = 204
                    response_data["message"] = "Nothing to update"
            else:
                response_data["code"] = 404
                response_data["message"] = "Warehouse not found!"                    
            
            return response_data
        except TypeError as e:
            logger.error(f"Datatype error ocurred while modifying the warehouse details:\n\n{str(e)}")
            raise e
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An error ocurred while modifying the warehouse details:\n\n{str(e)}")
            raise e
        
    def get_the_warehouse(self, warehouse_id):
        """Get the warehouse details
        """        
        
        try:
            data = dict()
            response_data = dict()
            logged_in_user = self.env.user
            
            warehouse = self.env['stock.warehouse'].search(
                [
                    ("id", "=", int(warehouse_id)),
                    ("company_id", "=", logged_in_user.company_id.id),
                    ("active", "in", [True, False])
                ]
            )
            
            if warehouse:
                data["id"] = warehouse.id
                data["name"] = warehouse.name
                data["code"] = warehouse.code
                data["active"] = warehouse.active
                data["partner"] = {"id": warehouse.partner_id.id, "name": warehouse.partner_id.name} if warehouse.partner_id else {}
                data["warehouse_view_location"] = {"id": warehouse.view_location_id.id, "name": warehouse.view_location_id.name} if warehouse.view_location_id else {}
                data["stock_location"] = {"id": warehouse.lot_stock_id.id, "name": warehouse.lot_stock_id.name} if warehouse.lot_stock_id else {}
                data["input_location"] = {"id": warehouse.wh_input_stock_loc_id.id, "name": warehouse.wh_input_stock_loc_id.name} if warehouse.wh_input_stock_loc_id else {}
                data["output_location"] = {"id": warehouse.wh_output_stock_loc_id.id, "name": warehouse.wh_output_stock_loc_id.name} if warehouse.wh_output_stock_loc_id else {}
                data["quality_control_location"] = {"id": warehouse.wh_qc_stock_loc_id.id, "name": warehouse.wh_qc_stock_loc_id.name} if warehouse.wh_qc_stock_loc_id else {}
                data["packing_location"] = {"id": warehouse.wh_pack_stock_loc_id.id, "name": warehouse.wh_pack_stock_loc_id.name} if warehouse.wh_pack_stock_loc_id else {}
                data["in_type"] = {"id": warehouse.in_type_id.id, "name": warehouse.in_type_id.name} if warehouse.in_type_id else {}
                data["out_type"] = {"id": warehouse.out_type_id.id, "name": warehouse.out_type_id.name} if warehouse.out_type_id else {}
                data["internal_type"] = {"id": warehouse.int_type_id.id, "name": warehouse.int_type_id.name} if warehouse.int_type_id else {}                    
                data["pick_type"] = {"id": warehouse.pick_type_id.id, "name": warehouse.pick_type_id.name} if warehouse.pick_type_id else {}
                data["pack_type"] = {"id": warehouse.pack_type_id.id, "name": warehouse.pack_type_id.name} if warehouse.pack_type_id else {}
                                    
                data["resupply_from_warehouse_ids"] = [
                    {
                        "id": wh.id, 
                        "name": wh.name 
                    } for wh in warehouse.resupply_wh_ids
                ] if warehouse.resupply_wh_ids else []
                                    
                response_data["code"] = 200
                response_data["message"] = "Success"
                response_data["data"] = data
            else:
                response_data["code"] = 404
                response_data["message"] = "Warehouse not found!"
            
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the warehouse details:\n\n{str(e)}")
            raise e
        
    def get_all_the_warehouses(self, query_params):
        """Get all the warehouses 
        """        
        
        try:
            response_data = dict()
            all_warehouses = []
            logged_in_user = self.env.user
            search_criteria = [("company_id", "=", logged_in_user.company_id.id)]
            
            if query_params.get("active") == True or query_params.get("active") == False:
                is_active = query_params.get("active")
                search_criteria.append(
                    ("active", "=", is_active)
                )
                            
            warehouses = self.env['stock.warehouse'].search(search_criteria, order='name asc')
            
            if warehouses:
                for warehouse in warehouses:
                    data = dict()
                    data["id"] = warehouse.id
                    data["name"] = warehouse.name
                    data["code"] = warehouse.code
                    data["active"] = warehouse.active
                    data["partner"] = {"id": warehouse.partner_id.id, "name": warehouse.partner_id.name} if warehouse.partner_id else {}
                    data["warehouse_view_location"] = {"id": warehouse.view_location_id.id, "name": warehouse.view_location_id.name} if warehouse.view_location_id else {}
                    data["stock_location"] = {"id": warehouse.lot_stock_id.id, "name": warehouse.lot_stock_id.name} if warehouse.lot_stock_id else {}
                    data["input_location"] = {"id": warehouse.wh_input_stock_loc_id.id, "name": warehouse.wh_input_stock_loc_id.name} if warehouse.wh_input_stock_loc_id else {}
                    data["output_location"] = {"id": warehouse.wh_output_stock_loc_id.id, "name": warehouse.wh_output_stock_loc_id.name} if warehouse.wh_output_stock_loc_id else {}
                    data["quality_control_location"] = {"id": warehouse.wh_qc_stock_loc_id.id, "name": warehouse.wh_qc_stock_loc_id.name} if warehouse.wh_qc_stock_loc_id else {}
                    data["packing_location"] = {"id": warehouse.wh_pack_stock_loc_id.id, "name": warehouse.wh_pack_stock_loc_id.name} if warehouse.wh_pack_stock_loc_id else {}
                    data["in_type"] = {"id": warehouse.in_type_id.id, "name": warehouse.in_type_id.name} if warehouse.in_type_id else {}
                    data["out_type"] = {"id": warehouse.out_type_id.id, "name": warehouse.out_type_id.name} if warehouse.out_type_id else {}
                    data["internal_type"] = {"id": warehouse.int_type_id.id, "name": warehouse.int_type_id.name} if warehouse.int_type_id else {}                    
                    data["pick_type"] = {"id": warehouse.pick_type_id.id, "name": warehouse.pick_type_id.name} if warehouse.pick_type_id else {}
                    data["pack_type"] = {"id": warehouse.pack_type_id.id, "name": warehouse.pack_type_id.name} if warehouse.pack_type_id else {}
                                        
                    data["resupply_from_warehouse_ids"] = [
                        {
                            "id": wh.id, 
                            "name": wh.name 
                        } for wh in warehouse.resupply_wh_ids
                    ] if warehouse.resupply_wh_ids else []
                    
                    all_warehouses.append(data)
                
                response_data["code"] = 200
                response_data["message"] = "Success"
                response_data["data"] = all_warehouses
            else:
                response_data["code"] = 404
                response_data["message"] = "Warehouse not found!"
            
            return response_data
        except SessionExpiredException as e:
            logger.error(f"The session has expired:\n\n{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the warehouses:\n\n{str(e)}")
            raise e
