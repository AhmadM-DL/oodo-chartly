import urllib.request
import json
import logging

_logger = logging.getLogger(__name__)

DEFAULT_MODEL = 'gpt-5.1'

class OpenAIClient:
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://api.openai.com/v1'
        self.timeout = 30
    
    def chat_completion(self, messages, model=DEFAULT_MODEL, max_tokens=1000, temperature=0.7, tools=None, tool_choice=None):
        try:

            data = {
                'model': model,
                'messages': messages,
            }

            if model in ["gpt-5-nano", "gpt-5.1"]:
                data["max_completion_tokens"] = max_tokens
                data['temperature'] = 1
            else:
                data["max_tokens"] = max_tokens
                data['temperature'] = temperature
            
            if tools:
                data['tools'] = tools
            if tool_choice:
                data['tool_choice'] = tool_choice
            
            req = urllib.request.Request(
                f'{self.base_url}/chat/completions',
                data=json.dumps(data).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
            )
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if 'choices' in result and len(result['choices']) > 0:
                    choice = result['choices'][0]
                    response_data = {
                        'success': True,
                        'content': choice['message'].get('content'),
                        'usage': result.get('usage', {}),
                        'model': result.get('model', model),
                        'finish_reason': choice.get('finish_reason')
                    }
                    
                    if 'tool_calls' in choice['message']:
                        response_data['tool_calls'] = choice['message']['tool_calls']
                    
                    return response_data
                else:
                    _logger.error(f"Unexpected API response format: {result}")
                    return {
                        'success': False,
                        'error': 'Unexpected response format from OpenAI API'
                    }
                    
        except urllib.error.HTTPError as e:
            error_msg = self._parse_http_error(e)
            _logger.error(f"OpenAI API HTTP error: {e.code} - {error_msg}")
            return {
                'success': False,
                'error': f'API request failed with status {e.code}: {error_msg}'
            }
            
        except urllib.error.URLError as e:
            _logger.error(f"OpenAI API URL error: {str(e)}")
            return {
                'success': False,
                'error': 'Request timeout or connection error'
            }
            
        except json.JSONDecodeError as e:
            _logger.error(f"Failed to parse API response: {str(e)}")
            return {
                'success': False,
                'error': 'Invalid response from API'
            }
            
        except Exception as e:
            _logger.error(f"Unexpected error calling OpenAI API: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def chat_completion_with_tools(self, messages, tools, model=DEFAULT_MODEL, max_tokens=1000, temperature=0.7, tool_choice='auto'):
        return self.chat_completion(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            tools=tools,
            tool_choice=tool_choice
        )
    
    def _parse_http_error(self, error):
        try:
            if hasattr(error, 'read'):
                error_body = json.loads(error.read().decode('utf-8'))
                if 'error' in error_body:
                    if isinstance(error_body['error'], dict):
                        return error_body['error'].get('message', str(error))
                    return str(error_body['error'])
            return str(error)
        except Exception:
            return str(error)
    
    @staticmethod
    def prepare_chat_history(chat_messages):
        messages = []
        for msg in chat_messages.sorted('created_at'):
            if msg.sender == 'user':
                messages.append({"role": "user", "content": msg.content})
            elif msg.sender == 'ai':
                messages.append({"role": "assistant", "content": msg.content})
        return messages
    
    @staticmethod
    def add_user_message(messages, user_content):
        return messages + [{"role": "user", "content": user_content}]
    
    @staticmethod
    def add_system_message(messages, system_content):
        return [{"role": "system", "content": system_content}] + messages 
    
    @staticmethod
    def add_tool_response(messages, tool_call_id, tool_name, tool_response):
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": json.dumps(tool_response) if isinstance(tool_response, dict) else str(tool_response)
        })
        return messages
    
    @staticmethod
    def create_function_tool(name, description, parameters, required):
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters":{
                    "type": "object",
                    "properties": parameters,
                    "required": required
                }
            }
        }


def get_openai_client(env):
    api_key = env['ir.config_parameter'].sudo().get_param('chartly.api_key')
    return OpenAIClient(api_key)