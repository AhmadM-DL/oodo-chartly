from odoo import models, fields

class OpenAISettings(models.Model):
    _name = 'openai.settings'
    _description = 'OpenAI Settings'

    api_key = fields.Char(string='OpenAI API Key', required=True, readonly=True)