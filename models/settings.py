from odoo import api, fields, models, _


class NaidashSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    
    openstreetmap_base_url = fields.Char(
        string = "OpenStreetMap Base URL",
        default = "https://nominatim.openstreetmap.org",
        help="The base URL for OpenStreetMap API"
    )
    
    mapbox_base_url = fields.Char(
        string = "Mapbox Base URL",
        default = "https://api.mapbox.com",
        help="The base URL for Mapbox API"
    )
    
    mapbox_access_token = fields.Char(
        string = "Mapbox Access Token",
        help="The access token for Mapbox API"
    )    
    
    
    @api.model
    def get_values(self):
        res = super(NaidashSettings, self).get_values()
        openstreetmap_url = self.env['ir.config_parameter'].sudo().get_param('naidash_courier.openstreetmap_base_url')
        mapbox_url = self.env['ir.config_parameter'].sudo().get_param('naidash_courier.mapbox_base_url')
        mapbox_token = self.env['ir.config_parameter'].sudo().get_param('naidash_courier.mapbox_access_token')
        
        res.update(
            {
                'openstreetmap_base_url': openstreetmap_url,
                'mapbox_base_url': mapbox_url,
                'mapbox_access_token': mapbox_token
            }
        )

        return res

    def set_values(self):
        res = super(NaidashSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('naidash_courier.openstreetmap_base_url', self.openstreetmap_base_url)
        self.env['ir.config_parameter'].sudo().set_param('naidash_courier.mapbox_base_url', self.mapbox_base_url)
        self.env['ir.config_parameter'].sudo().set_param('naidash_courier.mapbox_access_token', self.mapbox_access_token)
        
        return res
            