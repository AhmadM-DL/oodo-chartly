import os
from logging import getLogger

logger = getLogger(__name__)

QUERY_TO_PLOT_PROMPT_FILENAME = "query_to_plot_prompt.txt"

def get_query_to_plot_prompt():
    filepath = os.path.join(os.path.dirname(__file__), QUERY_TO_PLOT_PROMPT_FILENAME)
    with open(filepath, "r") as f:
        prompt = f.read()
    return prompt
        
def query_to_plot(client, query, sql_query: str)-> str:
    prompt = get_query_to_plot_prompt()
    messages = []
    messages = client.add_system_message(messages, prompt)
    messages = client.add_user_message(messages, f"Query: {query} \n SQL Query: {sql_query}")
    response = client.chat_completion(messages, temperature= 0.3,)
    response_content = response.get("content")
    logger.info(f"Query to Plot response content:\n{response_content}")
    request_cost = response.get("cost")
    return {"plot_script": response_content, "cost": request_cost}