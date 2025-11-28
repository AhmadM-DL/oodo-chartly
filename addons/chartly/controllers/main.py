from odoo import http
from odoo.http import request
import logging
import os
from odoo.addons.chartly.core.openai import get_openai_client
from odoo.addons.chartly.core.tools import get_tools

_logger = logging.getLogger(__name__)

PROMPT_FILENAME = "main_prompt.txt"

class ChartlyController(http.Controller):

    def _get_system_message(self):
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
            if not chat.title and not chat.messages and len(message_content.strip()) > 3:
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
            chat_history = openai_client.add_system_message(chat_history, self._get_system_message())
            chat_history = openai_client.add_user_message(chat_history, message_content)
            tools_map, tools_descriptions = get_tools()
            
            ai_result = openai_client.chat_completion_with_tools(chat_history, tools_descriptions, tools_map)
            
            # Extract cost from AI result
            ai_cost = ai_result.get('cost', 0)
            
            if ai_result.get('success'):
                ai_content = ai_result.get('content', 'No response from AI.')
            else:
                ai_content = f"Error: {ai_result.get('error', 'Unknown error')}"
            
            ai_message_dict = {
                'chat_id': chat_id,
                'content': ai_content,
                'sender': 'ai',
                'cost': ai_cost,
            }

            if "image" in ai_result:
                ai_message_dict.update({
                'has_image': True,
                'image': ai_result["image"]
            })

            # Create AI message
            ai_message = request.env['chartly.chat.message'].create(ai_message_dict)

            returned_ai_message = {
                    'id': ai_message.id,
                    'content': ai_message.content,
                    'sender': ai_message.sender,
                    'created_at': ai_message.created_at.isoformat() if ai_message.created_at else None,
                    'cost': ai_message.cost or 0,
                }
            if ai_message.has_image:
                returned_ai_message.update({"image": ai_message.image})

            # Refresh total_cost
            chat.invalidate_recordset(['total_cost'])

            return {
                'success': True,
                'user_message': {
                    'id': user_message.id,
                    'content': user_message.content,
                    'sender': user_message.sender,
                    'created_at': user_message.created_at.isoformat() if user_message.created_at else None,
                    'cost': 0,
                },
                'ai_message': returned_ai_message,
                'total_cost': chat.total_cost or 0,
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

            returned_messages = []
            for msg in messages:
                msg_dict = {
                    'id': msg.id,
                    'content': msg.content,
                    'sender': msg.sender,
                    'created_at': msg.created_at.isoformat() if msg.created_at else None,
                    'cost': msg.cost or 0,
                }
                if msg.has_image:
                    msg_dict.update({"image": msg.image})
                returned_messages.append(msg_dict)

            # Get total cost for the chat
            chat = request.env['chartly.chat'].browse(int(chat_id))
            total_cost = chat.total_cost if chat.exists() else 0
            
            return {
                'success': True,
                'messages': returned_messages,
                'total_cost': total_cost,
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

    @http.route('/chartly/update_title', type='json', auth='user', methods=['POST'], csrf=False)
    def update_title(self, chat_id, title):
        """Update chat title"""
        try:
            if not chat_id:
                return {'success': False, 'error': 'Missing chat_id parameter'}
            
            chat = request.env['chartly.chat'].browse(int(chat_id))
            if not chat.exists():
                return {'success': False, 'error': 'Chat not found'}
            
            chat.title = title or 'Untitled Chat'
            
            return {
                'success': True,
                'title': chat.title
            }
            
        except Exception as e:
            _logger.error(f"Error in update_title: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/chartly/get_chat_info', type='json', auth='user', methods=['POST'], csrf=False)
    def get_chat_info(self, chat_id):
        """Get chat info (title, created_at, total_cost)"""
        try:
            if not chat_id:
                return {'success': False, 'error': 'Missing chat_id parameter'}
            
            chat = request.env['chartly.chat'].browse(int(chat_id))
            if not chat.exists():
                return {'success': False, 'error': 'Chat not found'}
            
            return {
                'success': True,
                'title': chat.title,
                'created_at': chat.created_at.strftime('%Y-%m-%d %H:%M') if chat.created_at else '',
                'total_cost': chat.total_cost or 0,
            }
            
        except Exception as e:
            _logger.error(f"Error in get_chat_info: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/chartly/duplicate_chat', type='json', auth='user', methods=['POST'], csrf=False)
    def duplicate_chat(self, chat_id):
        """Duplicate a chat"""
        try:
            if not chat_id:
                return {'success': False, 'error': 'Missing chat_id parameter'}
            
            chat = request.env['chartly.chat'].browse(int(chat_id))
            if not chat.exists():
                return {'success': False, 'error': 'Chat not found'}
            
            new_chat = chat.copy({'title': f"{chat.title} (copy)"})
            
            return {
                'success': True,
                'chat_id': new_chat.id,
                'title': new_chat.title
            }
            
        except Exception as e:
            _logger.error(f"Error in duplicate_chat: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/chartly/delete_chat', type='json', auth='user', methods=['POST'], csrf=False)
    def delete_chat(self, chat_id):
        """Delete a chat"""
        try:
            if not chat_id:
                return {'success': False, 'error': 'Missing chat_id parameter'}
            
            chat = request.env['chartly.chat'].browse(int(chat_id))
            if not chat.exists():
                return {'success': False, 'error': 'Chat not found'}
            
            chat.unlink()
            
            return {'success': True}
            
        except Exception as e:
            _logger.error(f"Error in delete_chat: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/chartly/delete_all_chats', type='json', auth='user', methods=['POST'], csrf=False)
    def delete_all_chats(self):
        """Delete all chats"""
        try:
            chats = request.env['chartly.chat'].search([])
            chats.unlink()
            
            return {'success': True, 'deleted_count': len(chats)}
            
        except Exception as e:
            _logger.error(f"Error in delete_all_chats: {str(e)}")
            return {'success': False, 'error': str(e)}
