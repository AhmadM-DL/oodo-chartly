import os
from logging import getLogger
import re

logger = getLogger(__name__)

NL_TO_SQL_PROMPT_FILENAME = "nl_to_sql_prompt.txt"

def get_nl_to_sql_prompt():
    filepath = os.path.join(os.path.dirname(__file__), NL_TO_SQL_PROMPT_FILENAME)
    with open(filepath, "r") as f:
        prompt = f.read()
    return prompt
        
def nl_to_sql(client, query: str, models: list[str], fields: dict)-> dict:
    prompt = get_nl_to_sql_prompt()
    messages = []
    messages = client.add_system_message(messages, prompt)
    fields_str = ""
    for k, v in fields.items():
        fields_str += f"# {k}: {v}\n"
    messages = client.add_user_message(messages, f"Models: {models}\nFields:\n{fields_str}")
    messages = client.add_user_message(messages, f"Query: {query}")
    response = client.chat_completion(messages, temperature= 0.3,)
    sql_query = response.get("content")
    request_cost = response.get("cost")
    return {"sql_query": sql_query, "cost": request_cost}