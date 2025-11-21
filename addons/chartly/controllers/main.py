from odoo import http
from odoo.http import request
import logging
import os
from odoo.addons.chartly.core.openai import get_openai_client

_logger = logging.getLogger(__name__)

PROMPT_FILENAME = "main_prompt.txt"

class ChartlyController(http.Controller):

    def _get_system_message():
        filepath = os.path.join(os.path.dirname(__file__), PROMPT_FILENAME)
        with open(filepath, "r") as f:
            system_prompt = f.read()
        return system_prompt

    @http.route('/chartly/send_message', type='json', auth='user', methods=['POST'], csrf=False)
    def send_message(self, chat_id, message_content):
        """Send a message to the chat and get AI response"""
        try:
            if not chat_id or not message_content:
                return {'error': 'Missing required parameters'}
            
            chat = request.env['chartly.chat'].browse(int(chat_id))
            if not chat.exists():
                return {'error': 'Chat not found'}
            
            # Update title if this is the first message
            if not chat.messages and len(message_content.strip()) > 3:
                title = message_content.strip()[:50] + "..." if len(message_content.strip()) > 50 else message_content.strip()
                chat.title = title
            
            # Create user message
            user_message = request.env['chartly.chat.message'].create({
                'chat_id': chat_id,
                'content': message_content,
                'sender': 'user'
            })
            
            # Get AI response via OpenAIClient
            openai_client = get_openai_client(request.env)
            chat_history = openai_client.prepare_chat_history(chat.messages)
            chat_history = openai_client.add_system_message(self._get_system_message())
            chat_history = openai_client.add_user_message(message_content)
            
            ai_result = openai_client.chat_completion(chat_history, model="gpt-4")
            
            if ai_result.get('success'):
                ai_content = ai_result.get('content', 'No response from AI.')
            else:
                ai_content = f"Error: {ai_result.get('error', 'Unknown error')}"
            
            # Create AI message
            ai_message = request.env['chartly.chat.message'].create({
                'chat_id': chat_id,
                'content': ai_content,
                'sender': 'ai'
            })
            
            return {
                'success': True,
                'user_message': {
                    'id': user_message.id,
                    'content': user_message.content,
                    'sender': user_message.sender,
                    'created_at': user_message.created_at.isoformat() if user_message.created_at else None
                },
                'ai_message': {
                    'id': ai_message.id,
                    'content': ai_message.content,
                    'sender': ai_message.sender,
                    'created_at': ai_message.created_at.isoformat() if ai_message.created_at else None
                }
            }
            
        except Exception as e:
            _logger.error(f"Error in send_message: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/chartly/get_messages', type='json', auth='user', methods=['POST'], csrf=False)
    def get_messages(self, chat_id):
        """Get all messages for a chat"""
        try:
            if not chat_id:
                return {'success': False, 'error': 'Missing chat_id parameter'}
            
            messages = request.env['chartly.chat.message'].search([
                ('chat_id', '=', int(chat_id))
            ], order='created_at asc')
            
            return {
                'success': True,
                'messages': [{
                    'id': msg.id,
                    'content': msg.content,
                    'sender': msg.sender,
                    'created_at': msg.created_at.isoformat() if msg.created_at else None
                } for msg in messages]
            }
            
        except Exception as e:
            _logger.error(f"Error in get_messages: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/chartly/create_chat', type='json', auth='user', methods=['POST'], csrf=False)
    def create_chat(self, title=None):
        """Create a new chat"""
        try:
            chat = request.env['chartly.chat'].create({
                'title': title or 'New Chat'
            })
            
            return {
                'success': True,
                'chat_id': chat.id,
                'title': chat.title
            }
            
        except Exception as e:
            _logger.error(f"Error in create_chat: {str(e)}")
            return {'success': False, 'error': str(e)}
