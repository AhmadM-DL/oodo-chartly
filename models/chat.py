from odoo import models, fields, api

class Chat(models.Model):
    _name = "chartly.chat"
    _description = "Chartly Chat"
    _order = "created_at desc"

    title = fields.Char(string="Title", default="New Chat")
    created_at = fields.Datetime(string="Created At", default=fields.Datetime.now)
    messages = fields.One2many(
        comodel_name="chartly.chat.message",
        inverse_name="chat_id",
        string="Messages"
    )
    message_count = fields.Integer(string="Message Count", compute="_compute_message_count")
    # Add a dummy field for the widget to bind to
    chat_interface = fields.Char(string="Chat Interface", compute="_compute_chat_interface")
    total_cost = fields.Float(string="Total Cost", compute="_compute_total_cost")

    @api.depends('messages')
    def _compute_total_cost(self):
        for chat in self:
            chat.total_cost = sum(chat.messages.mapped('cost'))

    @api.depends('messages')
    def _compute_message_count(self):
        for chat in self:
            chat.message_count = len(chat.messages)

    def _compute_chat_interface(self):
        """Dummy compute method for the widget"""
        for chat in self:
            chat.chat_interface = "chat"

    @api.model
    def create_new_chat(self):
        """Create a new chat"""
        chat = self.create({
            'title': 'New Chat'
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'chartly.chat',
            'res_id': chat.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def get_chat_context(self):
        """Get context for the chat interface"""
        return {
            'chat_id': self.id,
            'title': self.title,
            'message_count': self.message_count,
            'total_cost': self.total_cost,
        }