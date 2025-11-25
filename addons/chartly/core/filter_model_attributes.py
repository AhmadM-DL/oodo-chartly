def get_filter_model_attributes_prompt(query, attributes):
    prompt = []
    prompt.append("You are a tool designed to filter out unusful attributes returned from an executing an sql as a result of a natural language query.")
    prompt.append(f"The query: {query}")
    prompt.append(f"The attributes: {attributes}")
    prompt.append("Only return the useful attributes as list of attributes seperated by new line.")
    prompt.append("What we mean by useful attributes are attributes that we would use to answer the query in a chatbot settings.")
    prompt.append("The more concise the better, because we are in a chat application.")
    return "\n".join(prompt)
        
def filter_attributes(client, query: str, attributes: list)-> dict:
    prompt = get_filter_model_attributes_prompt(query, attributes)
    messages = []
    messages = client.add_user_message(messages, prompt)
    response = client.chat_completion(messages, temperature= 0.3)
    response_content = response.get("content").strip().split("\n")
    request_cost = response.get("cost")
    return {"attributes": response_content, "cost": request_cost}