from odoo import http
from odoo.http import request
import urllib.request
import json
import logging

_logger = logging.getLogger(__name__)

class ChartlyController(http.Controller):

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
            
            # Get AI response
            ai_response = self._get_ai_response(chat, message_content)
            
            # Create AI message
            ai_message = request.env['chartly.chat.message'].create({
                'chat_id': chat_id,
                'content': ai_response,
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

    def _get_ai_response(self, chat, message_content):
        """Get response from OpenAI API"""
        api_key = request.env['ir.config_parameter'].sudo().get_param('chartly.api_key')
        
        if not api_key:
            return "Error: OpenAI API key not configured. Please configure it in Settings."
        
        try:
            # Prepare conversation history
            messages = []
            for msg in chat.messages.sorted('created_at'):
                if msg.sender == 'user':
                    messages.append({"role": "user", "content": msg.content})
                elif msg.sender == 'ai':
                    messages.append({"role": "assistant", "content": msg.content})
            
            # Add current message
            messages.append({"role": "user", "content": message_content})
            
            # Make API call
            data = {
                'model': 'gpt-3.5-turbo',
                'messages': messages,
                'max_tokens': 1000,
                'temperature': 0.7
            }
            
            req = urllib.request.Request(
                'https://api.openai.com/v1/chat/completions',
                data=json.dumps(data).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                else:
                    return "Error: Unexpected response format from OpenAI API"
                
        except urllib.error.HTTPError as e:
            error_msg = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
            _logger.error(f"OpenAI API HTTP error: {e.code} - {error_msg}")
            return f"Error: Failed to get AI response. Status code: {e.code}"
        except urllib.error.URLError as e:
            _logger.error(f"OpenAI API URL error: {str(e)}")
            return "Error: Request timeout or connection error. Please try again."
        except Exception as e:
            _logger.error(f"Error calling OpenAI API: {str(e)}")
            return f"Error: {str(e)}"