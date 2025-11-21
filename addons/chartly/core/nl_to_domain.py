import json, os
from logging import getLogger

logger = getLogger(__name__)

NL_TO_DOMAIN_PROMPT_FILENAME = "nl_to_domain_prompt.txt"
    
def is_formatted(query: dict) -> bool:
    domain = query.get("domain").lower()
    if not (domain.strip().startswith('[') and domain.strip().endswith(']')):
        return False
    return True
    
def is_safe(query: dict) -> bool:
    forbidden_keywords = [
            'write', 'unlink', 'delete', 'remove',
            'execute', 'sudo', 'env[', '.env', 'cr.execute',
            'commit', 'rollback', '__import__', 'eval', 'exec']
    domain = query.get("domain").lower()
    for keyword in forbidden_keywords:
        if keyword in domain:
            return False
    return True

def get_nl_to_domain_prompt():
    filepath = os.path.join(os.path.dirname(__file__), NL_TO_DOMAIN_PROMPT_FILENAME)
    with open(filepath, "r") as f:
        prompt = f.read()
    return prompt
        
def nl_to_domain(client, query: str, model: str, fields: list)-> dict:
    prompt = get_nl_to_domain_prompt()
    messages = []
    messages = client.add_system_message(messages, prompt)
    messages = client.add_user_message(messages, f"Model: {model}\nQuery: {query}\nFields: {fields}")
    response = client.chat_completion(messages, model="gpt-3.5-turbo", temperature= 0.3,)
    response_content = response.get("content")
    response_content = json.loads(response_content)
    if (not is_safe(response_content)):
        response_content["not_safe"] = True
    if (not is_formatted(response_content)):
        response_content["not_formatted"] = True
    return response_content