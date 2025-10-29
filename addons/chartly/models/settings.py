from odoo import models, fields

class Settings(models.TransientModel):
    _name = "chartly.settings"
    _description = "Chartly Settings"
    _inherit = 'res.config.settings'

    api_key = fields.Char(string="API Key", config_parameter='chartly.api_key', required=True)