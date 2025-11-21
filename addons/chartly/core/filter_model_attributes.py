def get_filter_model_attributes_prompt(query, model, attributes):
    prompt = []
    prompt.append("You are a tool designed to filter out unusful attributes returned from an odoo model as a result of a query.")
    prompt.append(f"The model: {model}")
    prompt.append(f"The query: {query}")
    prompt.append(f"The attributes: {attributes}")
    prompt.append("Only return the useful attributes as list of attributes seperated by new line.")
    prompt.append("What we mean by usful attributes are attributes that we would use to answer the query in a chatbot settings.")
    prompt.append("Example if the query asks for all invocies basic information would be required like: id, customer, date, company, and value ...")
    prompt.append("If explicit information exist get rid of the implements ones. i.e. if company name exists no need for the company id.")
    prompt.append("Avoid attributes used as foreign keys to other models mostly ids.")
    prompt.append("Remove all attributes not meant to be displayed.")
    prompt.append("Don't include redundant information.")
    prompt.append("The more concise the better, because we are in a chat application.")
    prompt.append("Unmercyfully remove attributes.")
    return "\n".join(prompt)
        
def filter_attributes(client, query: str, model: str, attributes: list)-> dict:
    prompt = get_filter_model_attributes_prompt(query, model, attributes)
    messages = []
    messages = client.add_user_message(messages, prompt)
    response = client.chat_completion(messages, temperature= 0.3)
    response_content = response.get("content")
    response_content = response_content.split()
    return response_content