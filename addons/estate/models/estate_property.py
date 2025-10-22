from odoo import models, fields

class EstateProperty(models.Model):
    _name = "estate_property"
    _description = "Estate Property Model"

    name = fields.Char(string="Property Name", required=True)
    description = fields.Text(string="Description")
    postcode = fields.Char(string="Postcode")
    date_availability = fields.Date(string="Date Availability")
    expected_price = fields.Float(string="Expected Price", required=True)
    selling_price = fields.Float(string="Selling Price")
    bedrooms = fields.Integer(string="Bedrooms", required=True)
    living_area = fields.Integer(string="Living Area (sqm)", required=True)
    facades = fields.Integer(string="Number of Facades", required=True)
    garage = fields.Boolean(string="Garage")
    garden_area = fields.Integer(string="Garden Area (sqm)")
    garden_orientation = fields.Selection(
        string="Garden Orientation",
        selection=[
            ('north', 'North'),
            ('south', 'South'),
            ('east', 'East'),
            ('west', 'West')
        ]
    )