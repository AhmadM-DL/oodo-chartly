import json, os
from logging import getLogger

logger = getLogger(__name__)

NL_TO_MODEL_PROMPT_FILENAME = "nl_to_model_prompt.txt"


def get_nl_to_model_prompt():
    filepath = os.path.join(os.path.dirname(__file__), NL_TO_MODEL_PROMPT_FILENAME)
    with open(filepath, "r") as f:
        prompt = f.read()
    return prompt
        
def nl_to_model(client, text: str)-> list[str]:
    prompt = get_nl_to_model_prompt()
    messages = []
    messages = client.add_system_message(messages, prompt)
    messages = client.add_user_message(messages, f"Query: {text}")
    response = client.chat_completion(messages, temperature= 0.3,)
    response_content = response.get("content")
    response_content = json.loads(response_content)
    models = response_content.get("models")
    request_cost = response.get("cost")
    return {"models": models, "cost": request_cost}