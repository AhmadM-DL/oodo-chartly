from odoo import models, fields, api

class ChatMessage(models.Model):
    _name = "chartly.chat.message"
    _description = "Chartly Chat Message"
    _order = "created_at asc"

    chat_id = fields.Many2one("chartly.chat", string="Chat", required=True, ondelete="cascade")
    content = fields.Text(string="Content", required=True)
    sender = fields.Selection(
        [("user", "User"), ("ai", "AI")],
        string="Sender",
        required=True
    )
    created_at = fields.Datetime(string="Created At", default=fields.Datetime.now)
    has_image = fields.Boolean(string="Has Image", default=False)
    image = fields.Binary(string="Image")