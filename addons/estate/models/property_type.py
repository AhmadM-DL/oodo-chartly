from odoo import models, fields

class PropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Property Type Model"

    name = fields.Char(string="Type Name", required=True)
    description = fields.Text(string="Description")