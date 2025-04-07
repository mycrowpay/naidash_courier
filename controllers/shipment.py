# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, route, SessionExpiredException
from odoo.service import security
from odoo.service.security import check_session

logger = logging.getLogger(__name__)

class NaidashShipment(http.Controller):
    @route('/api/v1/ship', methods=['POST'], auth='user', type='json')
    def create_shipment(self, **kw):
        """Create the shipment
        """ 

        try:            
            request_data = json.loads(request.httprequest.data)                        
            shipment_details = request.env['courier.shipment'].create_shipment(request_data)
            return shipment_details
        except Exception as e:
            logger.exception(f"The following error occurred while creating the shipment:\n\n{str(e)}")
            return {
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/ship/<int:shipment_id>', methods=['PATCH'], auth='user', type='json')
    def edit_shipment(self, shipment_id, **kw):
        """Edit the shipment details
        """ 
                
        try:
            request_data = json.loads(request.httprequest.data)
            shipment_details = request.env['courier.shipment'].edit_shipment(shipment_id, request_data)
            return shipment_details
        except TypeError as e:
            logger.error(f"This datatype error ocurred while modifying the shipment:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }        
        except Exception as e:
            logger.exception(f"This error occurred while modifying the shipment:\n\n{str(e)}")
            return {            
                "code": 500,
                "message": str(e)
            }
            
    @route('/api/v1/ship/<int:shipment_id>', methods=['GET'], auth='user', type='http')
    def get_shipment(self, shipment_id):
        """Get the shipment details
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:
            shipment_details = request.env['courier.shipment'].get_shipment(shipment_id)
            status_code = shipment_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": shipment_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": shipment_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the shipment details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/ship/<int:shipment_id>/start', methods=['GET'], auth='user', type='http')
    def start_shipping(self, shipment_id):
        """Start shipping the item
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:
            shipment_details = request.env['courier.shipment'].start_shipping(shipment_id)
            status_code = shipment_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": shipment_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": shipment_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred when starting to ship:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/ship/<int:shipment_id>/finish', methods=['GET'], auth='user', type='http')
    def finish_shipping(self, shipment_id):
        """Start shipping the item
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:
            shipment_details = request.env['courier.shipment'].finish_shipping(shipment_id)
            status_code = shipment_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": shipment_details
                    }
                )

                return request.make_response(data, headers, status=status_code)                 
            else:
                data = json.dumps(
                    {
                        "result": shipment_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred when starting to ship:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)