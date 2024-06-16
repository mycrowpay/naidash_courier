import logging

from datetime import datetime
from odoo import models, fields, api, _
from odoo.http import request
from odoo.exceptions import ValidationError, UserError


logger = logging.getLogger(__name__)


class NaidashCourier(models.Model):
    _inherit = "courier.custom"


    # Sender's Details
    sender_name_id = fields.Many2one(
        'res.partner',
        string = "Sender's Name",
        required = False
    )
    
    sender_street = fields.Text(
        string = "Sender's Street",
        required = False
    )
    
    sender_zip = fields.Char(
        string = "Sender's Zip Code",
        required = False
    )
    
    sender_city = fields.Char(
        string = "Sender's City",
        required = False
    )
    
    sender_state_id = fields.Many2one(
        "res.country.state",
        string = "Sender's State",
        domain = "[('country_id', '=', sender_country_id)]",
        required = False
    )
    
    sender_country_id = fields.Many2one(
        'res.country',
        string = "Sender's Country",
        required = False
    )
    
    sender_mobile = fields.Char(
        string = "Sender's Mobile No",
        required = False
    )
    
    sender_email = fields.Char(
        string = "Sender's Email",
        required = False
    )
    
    # Receiver's Details
    receiver_name_id = fields.Many2one(
        'res.partner',
        string = "Receiver's Name",
        required = False
    )
        
    receiver_name = fields.Char(
        string = "Receiver Name",
        required = False
    )
    
    receiver_street = fields.Text(
        string = "Receiver's Street",
        required = False
    )
    
    receiver_zip = fields.Char(
        string = "Receiver's Zip code",
        required = False
    )
    
    receiver_city = fields.Char(
        string = "Receiver's City",
        required = False
    )
    
    receiver_state = fields.Char(
        string = "Receiver's State",
        required = False
    )
    
    receiver_country = fields.Char(
        string = "Receiver's Country",
        required = False
    )
    
    receiver_mobile = fields.Char(
        string = "Receiver's Mobile No",
        required = False
    )
    
    receiver_email = fields.Char(
        string = "Receiver's Email",
        required = False
    )
    
    receiver_state_id = fields.Many2one(
        "res.country.state",
        string = "Receiver's State",
        domain = "[('country_id', '=', receiver_country_id)]",
        required = False
    )
    
    receiver_country_id = fields.Many2one(
        'res.country',
        string = "Receiver's Country",
        required = False
    )    
            
    is_drop_shipping = fields.Boolean(
        string = "Requires Dropshipping?",
        default = False,
        help="If set to true, dropshipping services are required otherwise the dropshipping services are not required"
    )
    
    is_receiver_invoice = fields.Boolean(
        string = "Invoice The Receiver?",
        default = True,
        help="If set to true, the receiver will be invoiced otherwise the sender will be invoiced"
    )
    
    @api.model
    def create(self, vals):        
        if vals.get('name', _('New')) == _('New'):
            milliseconds = (datetime.now()).strftime("%f")[:-3]
            created_date = fields.Datetime.context_timestamp(self, fields.Datetime.now()).strftime("%Y%m%d%H%M%S")
            vals['name'] = f"CR-{created_date}{milliseconds}"
        res = super(NaidashCourier, self).create(vals)
        return res
    
    @api.onchange('receiver_name_id')
    def onchange_receiver_contact_info_custom(self):
        if self.receiver_name_id:
            self.receiver_street = self.receiver_name_id.street
            self.receiver_street2 = self.receiver_name_id.street2
            self.receiver_city = self.receiver_name_id.city
            self.receiver_state_id = self.receiver_name_id.state_id
            self.receiver_zip = self.receiver_name_id.zip
            self.receiver_country_id = self.receiver_name_id.country_id
            self.receiver_mobile = self.receiver_name_id.phone
            self.receiver_email = self.receiver_name_id.email
            