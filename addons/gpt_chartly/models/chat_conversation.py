from odoo import models, fields

class ChatConversation(models.Model):
    _name = 'openai.chat.conversation'
    _description = 'Chat Conversation'

    title = fields.Char(string='Chat Title', required=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    message_ids = fields.One2many('openai.chat.message', 'conversation_id', string='Messages')

    def create_chat(self, title):
        return self.create({'title': title})