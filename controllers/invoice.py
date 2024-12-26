# -*- coding: utf-8 -*-
from datetime import datetime
import json
import logging

from odoo import http
from odoo.http import Controller, request, route, SessionExpiredException, content_disposition
from odoo.service import security
from werkzeug.http import HTTP_STATUS_CODES
from werkzeug.exceptions import (NotFound, BadRequest, Unauthorized, HTTPException, Forbidden, 
                                 MethodNotAllowed, RequestTimeout, Conflict, UnprocessableEntity, 
                                 InternalServerError, GatewayTimeout, ServiceUnavailable)
from odoo.exceptions import UserError, MissingError, AccessError, AccessDenied

logger = logging.getLogger(__name__)

class NaidashInvoice(Controller):
    @route('/api/v1/naidash/invoice', methods=['POST'], auth='user', type='json')
    def create_invoice_from_a_sales_order(self, **kw):
        """Create Invoice from Sales Order
        """ 
                        
        try:
            request_data = json.loads(request.httprequest.data)                        
            invoice_details = request.env['account.move'].create_invoice_from_sales_order(request_data)
            return invoice_details
        except TypeError as e:
            logger.error(f"This datatype error ocurred while creating the invoice:\n\n{str(e)}")
            return {                
                "code": 422,
                "message": str(e)
            }      
        except Exception as e:
            logger.exception(f"This error occurred while creating the invoice:\n\n{str(e)}")
            if "HTTPSConnectionPool" in str(e):
                return {
                    "code": 504,
                    "message": "Check your internet connection"
                }
            else:
                return {
                    "code": 500,
                    "message": str(e)
                }
            
    @route('/api/v1/naidash/invoice/<int:invoice_id>', methods=['GET'], auth='user', type='http')
    def get_invoice(self, invoice_id):
        """Get the invoice details
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:
            invoice_details = request.env['account.move'].get_an_invoice(invoice_id)
            status_code = invoice_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": invoice_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:
                data = json.dumps(
                    {
                        "result": invoice_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the invoice details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/naidash/invoice', methods=['GET'], auth='user', type='http')
    def get_all_invoices(self):
        """
        Returns all invoices based on the query parameter(s).
        """ 
        
        headers = [('Content-Type', 'application/json')]
                
        try:
            query_params = dict()
            
            partner_id = request.params.get('partner_id')
            stage = request.params.get('stage')
            due_date_from = request.params.get('due_date_from')
            due_date_to = request.params.get('due_date_to')
            created_date_from = request.params.get('created_date_from')
            created_date_to = request.params.get('created_date_to')
            
            if partner_id:
                query_params["partner_id"] = int(partner_id)
            if stage:
                query_params["stage"] = stage
            if due_date_from and due_date_to:
                query_params["due_date_from"] = datetime.strptime(due_date_from, "%Y-%m-%d")
                query_params["due_date_to"] = datetime.strptime(due_date_to, "%Y-%m-%d")
            if created_date_from and created_date_to:
                query_params["created_date_from"] = datetime.strptime(created_date_from, "%Y-%m-%d")
                query_params["created_date_to"] = datetime.strptime(created_date_to, "%Y-%m-%d")
            
            if not query_params:
                data = json.dumps(
                    {
                        "error": {
                            "code": 400,
                            "message": "Bad Request"
                        }
                    }
                )

                return request.make_response(data, headers, status=400)
            
            invoice_details = request.env['account.move'].get_all_invoices(query_params)
            status_code = invoice_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": invoice_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:                
                data = json.dumps(
                    {
                        "result": invoice_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the invoices:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/naidash/invoice/<int:invoice_id>/confirm', methods=['GET'], auth='user', type='http')
    def confirm_the_invoice(self, invoice_id):
        """Confirm the invoice details
        """      
                
        headers = [('Content-Type', 'application/json')]
        try:
            invoice_details = request.env['account.move'].confirm_the_sales_order_invoice(invoice_id)
            status_code = invoice_details.get("code")
            
            if status_code != 200:
                data = json.dumps(
                    {
                        "error": invoice_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:
                data = json.dumps(
                    {
                        "result": invoice_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while confirming the invoice:\n\n{str(e)}")
            if "HTTPSConnectionPool" in str(e):
                data = json.dumps(
                    {
                        "error": {
                            "code": 504,
                            "message": "Check your internet connection"
                        }
                    }
                )
            else:
                data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
                
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/naidash/invoice/<int:invoice_id>/cancel', methods=['GET'], auth='user', type='http')
    def cancel_the_invoice(self, invoice_id):
        """Cancel the invoice
        """      
                
        headers = [('Content-Type', 'application/json')]
        try:
            invoice_details = request.env['account.move'].cancel_the_sales_order_invoice(invoice_id)
            status_code = invoice_details.get("code")
            
            if status_code != 200:
                data = json.dumps(
                    {
                        "error": invoice_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:
                data = json.dumps(
                    {
                        "result": invoice_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while cancelling the invoice:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/naidash/invoice/<int:invoice_id>/draft', methods=['GET'], auth='user', type='http')
    def reset_the_invoice_to_draft(self, invoice_id):
        """Reset a posted/cancelled invoice to draft
        """      
                
        headers = [('Content-Type', 'application/json')]
        try:
            invoice_details = request.env['account.move'].reset_the_sales_order_invoice_to_draft(invoice_id)
            status_code = invoice_details.get("code")
            
            if status_code != 200:
                data = json.dumps(
                    {
                        "error": invoice_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
            else:
                data = json.dumps(
                    {
                        "result": invoice_details
                    }
                )

                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while setting the invoice to draft:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @http.route('/api/v1/naidash/invoice/<int:invoice_id>/download', methods=['GET'], auth='user', type='http')
    def download_invoice(self, invoice_id):
        """Download a PDF version of the invoice"""
        
        headers = [('Content-Type', 'application/json')]
                
        try:
            invoice_details = request.env['account.move'].download_the_sales_order_invoice(invoice_id)
            status_code = invoice_details.get("code")
            document = invoice_details.get("data")
            
            if status_code == 200:
                headers = invoice_details.get("headers")
                return request.make_response(document, headers, status=status_code)
            else:
                data = json.dumps(
                    {
                        "error": invoice_details
                    }
                )
                
                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while downloading the invoice:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
