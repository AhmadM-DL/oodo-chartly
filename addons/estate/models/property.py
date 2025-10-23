import datetime
from odoo import models, fields

class Property(models.Model):
    _name = "estate.property"
    _description = "Property Model"

    def _default_date_availability(self):
        today = fields.Date.today()
        return today + datetime.timedelta(days=90)
    
    def _default_seller(self):
        return self.env.user.partner_id.id


    name = fields.Char(string="Property Name", required=True)
    description = fields.Text(string="Description")

    buyer_id = fields.Many2one("res.partner", string="Buyer", copy=False)
    seller_id = fields.Many2one("res.partner", string="Seller", default= _default_seller)

    property_type_id = fields.Many2one("estate.property.type", string="Property Type")

    postcode = fields.Char(string="Postcode")
    date_availability = fields.Date(string="Date Availability",
                                    copy= False,
                                    default=_default_date_availability)
    expected_price = fields.Float(string="Expected Price", required=True)
    selling_price = fields.Float(string="Selling Price",
                                 copy=False,
                                 readonly=True)
    bedrooms = fields.Integer(string="Bedrooms", required=True, default=2)
    living_area = fields.Integer(string="Living Area (sqm)", required=True)
    facades = fields.Integer(string="Facades", required=True)
    garage = fields.Boolean(string="Garage")
    garden = fields.Boolean(string="Garden")
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
    state = fields.Selection(
        string="Status",
        selection=[
            ('new', 'New'),
            ('offer_received', 'Offer Received'),
            ('offer_accepted', 'Offer Accepted'),
            ('sold', 'Sold'),
            ('canceled', 'Canceled')
        ],
        default='new'
    )
    active = fields.Boolean(string="Active", default=True)