from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    api_key = fields.Char(string="API Key", config_parameter='chartly.api_key')
    model = fields.Selection(
        selection=[ ('gpt-3.5-turbo', 'GPT-3.5 Turbo'), ('gpt-4.1', 'GPT-4.1'), ('gpt-5-nano', 'GPT-5 Nano'), ('gpt-5.1', 'GPT-5.1') ],
        string="AI Model",
        config_parameter='chartly.model')