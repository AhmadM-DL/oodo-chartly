from typing import Callable
import urllib.request
import json
import logging

logger = logging.getLogger(__name__)

PRICING = {
    'gpt-5.1': {
        'input_per_1M': 1.25,
        'output_per_1M': 10.00,
        'cached_per_1M': 0.125
    },
    'gpt-5-nano': {
        'input_per_1M': 0.05,
        'output_per_1M': 0.40,
        'cached_per_1M': 0.005
    },
    'gpt-4.1': {
        'input_per_1M': 2.00,
        'output_per_1M': 8.00,
        'cached_per_1M': 0.5 
    },
    'gpt-3.5-turbo': {
        'input_per_1M': 0.50,
        'output_per_1M': 1.50,
        'cached_per_1M': 0      # no cached-token pricing provided
    }
}

class OpenAIClient:
    
    def __init__(self, api_key, model):
        self.api_key = api_key
        self.base_url = 'https://api.openai.com/v1'
        self.timeout = 30
        self.model = model

    def chat_completion(self, messages, max_tokens=1000, temperature=0.7, tools=None, tool_choice=None):
        try:

            data = {
                'model': self.model,
                'messages': messages,
            }

            if self.model in ["gpt-5-nano", "gpt-5.1"]:
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
                   
                    usage = result.get('usage', {})
                    logger.info(f"OpenAI API response usage: {usage}")

                    response_data = {
                        'success': True,
                        'content': choice['message'].get('content'),
                        'usage': usage,
                        'cost': self._compute_request_cost(self.model, usage),
                        'model': result.get('model', self.model),
                        'finish_reason': choice.get('finish_reason')
                    }
                    
                    if 'tool_calls' in choice['message']:
                        response_data['tool_calls'] = choice['message']['tool_calls']
                    
                    return response_data
                else:
                    logger.error(f"Unexpected API response format: {result}")
                    return {
                        'success': False,
                        'error': 'Unexpected response format from OpenAI API'
                    }
                    
        except urllib.error.HTTPError as e:
            error_msg = self._parse_http_error(e)
            logger.error(f"OpenAI API HTTP error: {e.code} - {error_msg}")
            return {
                'success': False,
                'error': f'API request failed with status {e.code}: {error_msg}'
            }
            
        except urllib.error.URLError as e:
            logger.error(f"OpenAI API URL error: {str(e)}")
            return {
                'success': False,
                'error': 'Request timeout or connection error'
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response: {str(e)}")
            return {
                'success': False,
                'error': 'Invalid response from API'
            }
            
        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI API: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def chat_completion_with_tools(self, messages, tools_descriptions, tools, max_tokens=1000, temperature=0.7, tool_choice='auto'):
        history = messages.copy()
        tool_generated_image= None
        cost = 0

        logger.debug(f"Passed messages: \n {history}")

        while True:
            logger.info(f"Calling chat completion")
            response = self.chat_completion(history, max_tokens=max_tokens, temperature=temperature, tools=tools_descriptions, tool_choice=tool_choice)
            
            logger.info(f"Chat completion response: {response}")
            if response.get('tool_calls') is None:
                logger.info(f"Chat compeltion with tools ended")
                response["cost"] = cost + response.get("cost", 0)
                if tool_generated_image:
                    response["image"] = tool_generated_image
                return response
            
            # if len(response.get('tool_calls')) > 1:
            #     logger.error("Multiple tool calls in a single response are not supported.")
            #     response["cost"] = cost + response.get("cost", 0)
            #     response["success"] = False
            #     response["error"] = "Failed to call a tool" #"Multiple tool calls in a single response are not supported."
            #     return response
            
            history = self.add_tool_call(history, response['tool_calls'][0])
            
            # Call the tool
            tool_name = response['tool_calls'][0]['function']['name']
            tool_input = response['tool_calls'][0]['function']['arguments']
            tool_input = json.loads(tool_input)

            if tool_name in [tool['function']['name'] for tool in tools_descriptions]:

                tool_map = tools.get(tool_name, None)
                # if not tool_map:
                #     response["cost"] = cost + response.get("cost", 0)
                #     response["success"] = False
                #     response["error"] = "Failed to call a tool" # f"Tool {tool_name} is not in passed tools"
                #     return response 
                
                tool_return_type = tool_map.get("return_type")
                tool_callable = tool_map.get("tool_callable")
                
                tool_response = self.execute_tool(tool_callable, tool_input)

                if tool_return_type=="text":
                    tool_content = tool_response.get("text")
                elif tool_return_type=="image":
                    tool_content = tool_response.get("text")
                    tool_generated_image = tool_response.get("image")
                else:
                    tool_content = tool_response
                
                cost += tool_response.get('cost', 0)
                history = self.add_tool_response(history, response['tool_calls'][0].get('id'), tool_name, tool_content)
          
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
        
    def _compute_request_cost(self, model, usage):
        input_tokens = usage.get('prompt_tokens', 0)
        output_tokens = usage.get('completion_tokens', 0)
        cached_tokens = usage.get('prompt_tokens_details', {}).get('cached_tokens', 0)
        if model not in PRICING.keys():
            logger.warning(f"Model {model} not found in pricing list.")
            return -1.0
        pricing = PRICING.get(model)
        input_tokens_cost = pricing['input_per_1M'] * (input_tokens / 1000000)
        cached_tokens_cost = pricing['cached_per_1M'] * (cached_tokens / 1000000)
        output_tokens_cost = pricing['output_per_1M'] * (output_tokens / 1000000)
        cost = input_tokens_cost + cached_tokens_cost + output_tokens_cost
        logger.info(f"Computed cost: {cost}")
        return round(cost, 5)
    
    def execute_tool(self, function: Callable, tool_input):
        try:
            result = function(**tool_input)
            return result
        except Exception as e:
            logger.error(f"Error executing tool {function}: {str(e)}")
            return {"text": f"Error executing tool {function}: {str(e)}", "error": True, "cost": 0}

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
    def add_assistant_message(messages, assistant_content):
        return messages + [{"role": "assistant", "content": assistant_content}]
    
    @staticmethod
    def add_tool_call(messages, tool_call):
        messages.append({
            "role": "assistant",
            "tool_calls": [{
                "id": tool_call.get('id'),
                "type": 'function',
                "function":{
                    "name": tool_call.get('function').get("name"),
                    "arguments": tool_call.get('function').get("arguments")
                }
            }]
        })
        return messages
    
    @staticmethod
    def add_tool_response(messages, tool_call_id, tool_name, tool_response_content):
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": tool_response_content
        })
        return messages
    
def create_function_tool(name, description, parameters, required):
    tool_description = {
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
    return tool_description

def get_openai_client(env):
    api_key = env['ir.config_parameter'].sudo().get_param('chartly.api_key')
    model = env['ir.config_parameter'].sudo().get_param('chartly.model')
    return OpenAIClient(api_key, model)