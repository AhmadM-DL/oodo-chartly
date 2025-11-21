import json, os
from logging import getLogger

logger = getLogger(__name__)

ALLOWED_ODOO_MODELS_FILENAME = "allowed_odoo_models.txt"
NL_TO_MODEL_PROMPT_FILENAME = "nl_to_model_prompt.txt"

def get_allowed_odoo_models():
    filepath = os.path.join(os.path.dirname(__file__), ALLOWED_ODOO_MODELS_FILENAME)
    with open(filepath, "r") as f:
        allowed_models = f.read().split()
    return allowed_models
    
def is_restricted(model: str) -> bool:
    allowed_models = get_allowed_odoo_models()
    if model in allowed_models:
        return True
    else:
        return False

def get_nl_to_model_prompt():
    filepath = os.path.join(os.path.dirname(__file__), NL_TO_MODEL_PROMPT_FILENAME)
    with open(filepath, "r") as f:
        prompt = f.read()
    return prompt
        
def nl_to_model(client, text: str)-> dict:
    prompt = get_nl_to_model_prompt()
    messages = []
    messages = client.add_system_message(messages, prompt)
    messages = client.add_user_message(messages, f"Query: {text}")
    response = client.chat_completion(messages, model="gpt-3.5-turbo", temperature= 0.3,)
    response_content = response.get("content")
    response_content = json.loads(response_content)
    models = response_content.get("models")
    all_restricted = True
    for m in models:
        if not is_restricted(m):
            all_restricted = False
            break
    if not all_restricted:
        response_content["not_restricted"] = True
    return response_content