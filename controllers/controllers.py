# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

import json
import logging


logger = logging.getLogger(__name__)

class NaidashCourier(http.Controller):
    @http.route('/api/v1/naidash/stage', methods=['POST'], auth='user', type='json')
    def create_stage(self, **kw):
        """Creates a stage"""
                        
        try:
            request_data = json.loads(request.httprequest.data)                        
            create_courier_stage = request.env['courier.stage.custom'].create_stage(request_data)
            return create_courier_stage
        except Exception as e:
            logger.exception(f"Error: The following error occurred while creating the stage:\n\n{str(e)}")
            return {                
                "status_code": 500,
                "error": str(e)
            }
            