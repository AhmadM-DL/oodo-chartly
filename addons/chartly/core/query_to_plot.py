import os
from logging import getLogger

logger = getLogger(__name__)

QUERY_TO_PLOT_PROMPT_FILENAME = "query_to_plot_prompt.txt"

def get_query_to_plot_prompt():
    filepath = os.path.join(os.path.dirname(__file__), QUERY_TO_PLOT_PROMPT_FILENAME)
    with open(filepath, "r") as f:
        prompt = f.read()
    return prompt
        
def query_to_plot(client, query, data_attributes: str)-> str:
    prompt = get_query_to_plot_prompt()
    messages = []
    messages = client.add_system_message(messages, prompt)
    messages = client.add_user_message(messages, f"Query: {query} \n Data Attributes: {data_attributes}")
    response = client.chat_completion(messages, model="gpt-3.5-turbo", temperature= 0.3,)
    response_content = response.get("content")
    return response_content