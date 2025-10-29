from odoo import models, fields, api

class ChatMessage(models.Model):
    _name = 'openai.chat.message'
    _description = 'Chat Message'

    conversation_id = fields.Many2one('openai.chat.conversation', string='Conversation', required=True)
    sender = fields.Selection([('user', 'User'), ('ai', 'AI')], string='Sender', required=True)
    message = fields.Text(string='Message', required=True)
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now)

    @api.model
    def create(self, vals):
        # Ensure the message is sent to OpenAI API and get the response
        if vals.get('sender') == 'user':
            api_key = self.env['openai.settings'].get_api_key()
            response = self._send_to_openai_api(vals.get('message'), api_key)
            vals['message'] = response
        return super(ChatMessage, self).create(vals)

    def _send_to_openai_api(self, user_message, api_key):
        # Logic to send the user message to OpenAI API and return the response
        # This is a placeholder for the actual API call
        return "AI response to: " + user_message  # Replace with actual API call logic