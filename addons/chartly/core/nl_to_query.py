import json, os
from logging import getLogger

logger = getLogger(__name__)

ALLOWED_ODOO_MODELS_FILENAME = "allowed_odoo_models.txt"
NL_TO_QUERY_PROMPT_FILENAME = "nl_to_query_prompt.txt"

def get_allowed_odoo_models():
    filepath = os.path.join(os.path.dirname(__file__), ALLOWED_ODOO_MODELS_FILENAME)
    with open(filepath, "r") as f:
        allowed_models = f.read().split()
    return allowed_models
    
def is_restricted(query: dict) -> bool:
    allowed_models = get_allowed_odoo_models()
    if query.get("model") in allowed_models:
        return True
    else:
        return False
    
def is_formatted(query: dict) -> bool:
    domain = query.get("domain").lower()
    if not (domain.strip().startswith('[') and domain.strip().endswith(']')):
        return False
    return True
    
def is_safe(query: dict) -> bool:
    forbidden_keywords = [
            'write', 'unlink', 'create', 'delete', 'remove',
            'execute', 'sudo', 'env[', '.env', 'cr.execute',
            'commit', 'rollback', '__import__', 'eval', 'exec']
    domain = query.get("domain").lower()
    for keyword in forbidden_keywords:
        if keyword in domain:
            return False
    return True

def get_nl_to_query_prompt():
    filepath = os.path.join(os.path.dirname(__file__), NL_TO_QUERY_PROMPT_FILENAME)
    with open(filepath, "r") as f:
        prompt = f.read()
    return prompt
        
def nl_to_query(client, text: str)-> dict:
    prompt = get_nl_to_query_prompt()
    messages = []
    messages = client.add_system_message(messages, prompt)
    messages = client.add_user_message(messages, f"Query: {text}")
    # logger.info(messages)
    response = client.chat_completion(messages, model="gpt-3.5-turbo", temperature= 0.3,)
    response_content = response.get("content")
    response_content = json.loads(response_content)
    if (not is_restricted(response_content)):
        response_content["not_restricted"] = True
    if (not is_safe(response_content)):
        response_content["not_safe"] = True
    if (not is_formatted(response_content)):
        response_content["not_formatted"] = True
    return response_content