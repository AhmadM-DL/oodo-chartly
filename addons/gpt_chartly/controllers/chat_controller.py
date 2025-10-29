from odoo import http
from odoo.http import request
import requests

class ChatController(http.Controller):

    @http.route('/openai_chat/create_chat', type='json', auth='user')
    def create_chat(self, title):
        chat = request.env['chat.conversation'].create({
            'title': title,
            'date': fields.Datetime.now(),
        })
        return {'chat_id': chat.id}

    @http.route('/openai_chat/get_chat_history', type='json', auth='user')
    def get_chat_history(self, chat_id):
        chat = request.env['chat.conversation'].browse(chat_id)
        messages = chat.message_ids.read(['content', 'timestamp'])
        return {'messages': messages}

    @http.route('/openai_chat/send_message', type='json', auth='user')
    def send_message(self, chat_id, message_content):
        chat = request.env['chat.conversation'].browse(chat_id)
        api_key = request.env['openai.settings'].search([], limit=1).api_key
        
        # Send message to OpenAI API
        response = requests.post(
            'https://api.openai.com/v1/completions',
            headers={'Authorization': f'Bearer {api_key}'},
            json={
                'model': 'text-davinci-003',
                'prompt': message_content,
                'max_tokens': 150
            }
        )
        
        response_data = response.json()
        openai_response = response_data.get('choices')[0].get('text').strip()

        # Create a new message in the chat
        request.env['chat.message'].create({
            'conversation_id': chat.id,
            'content': message_content,
            'is_user': True,
        })
        request.env['chat.message'].create({
            'conversation_id': chat.id,
            'content': openai_response,
            'is_user': False,
        })

        return {'response': openai_response}