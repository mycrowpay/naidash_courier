# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, route, SessionExpiredException
from odoo.service import security
from odoo.service.security import check_session

logger = logging.getLogger(__name__)

class NaidashStockLot(http.Controller):
    @route('/api/v1/stock_lot', methods=['POST'], auth='user', type='json')
    def create_stock_lot(self, **kw):
        """Create the stock lot details
        """ 

        try:            
            request_data = json.loads(request.httprequest.data)                        
            stock_lot_details = request.env['stock.lot'].create_the_stock_lot(request_data)
            return stock_lot_details
        except Exception as e:
            logger.exception(f"The following error occurred while creating the stock lot details:\n\n{str(e)}")
            return {
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/stock_lot/<int:stock_lot_id>', methods=['PATCH'], auth='user', type='json')
    def edit_stock_lot(self, stock_lot_id, **kw):
        """Edit the stock lot details
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            stock_lot_details = request.env['stock.lot'].edit_the_stock_lot(stock_lot_id, request_data)
            return stock_lot_details
        except TypeError as e:
            logger.error(f"This datatype error ocurred while modifying the stock lot details:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }        
        except Exception as e:
            logger.exception(f"This error occurred while modifying the stock lot details:\n\n{str(e)}")
            return {            
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/stock_lot/<int:stock_lot_id>', methods=['GET'], auth='user', type='http')
    def get_stock_lot(self, stock_lot_id):
        """Get the stock lot details
        """ 
                
        headers = [('Content-Type', 'application/json')]
        
        try:
            stock_lot_details = request.env['stock.lot'].get_the_stock_lot(stock_lot_id)
            status_code = stock_lot_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": stock_lot_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": stock_lot_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the stock lot details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/stock_lot', methods=['GET'], auth='user', type='http')
    def get_stock_lots(self):
        """
        Returns all the stock lots
        """ 
        
        headers = [
            ('Content-Type', 'application/json')
        ]
                
        try:           
            stock_lot_details = request.env['stock.lot'].get_all_the_stock_lots()
            status_code = stock_lot_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": stock_lot_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:                
                data = json.dumps(
                    {
                        "result": stock_lot_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the stock lots:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
            