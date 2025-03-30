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
