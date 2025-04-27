import logging
import pytz
from datetime import datetime, date, timedelta
from odoo import models, fields, api, _
from odoo.http import request
from odoo.exceptions import ValidationError, UserError

logger = logging.getLogger(__name__)

class NaidashCourierLine(models.Model):
    _inherit = "courier.line.custom"
    
    quantity = fields.Float(string = "Quantity", tracking=True)


    @api.depends('product_id', 'quantity')
    def _compute_courier_subtotal(self):
        for rec in self:
            rec.total_weight = 0
            rec.volumetric_weight = 0
            rec.total_volumetric_weight = 0
            rec.weight_cost = 0
            rec.volumetric_weight_cost = 0
            rec.courier_subtotal = rec.product_id.lst_price * rec.quantity