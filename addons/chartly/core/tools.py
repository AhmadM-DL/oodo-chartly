from odoo.addons.chartly.core.utils import get_model_fields
from odoo.addons.chartly.core.utils import extract_script_as_fct
from odoo.addons.chartly.core.openai import get_openai_client
from odoo.addons.chartly.core.filter_model_attributes import filter_attributes
from odoo.addons.chartly.core.nl_to_domain import nl_to_domain
from odoo.addons.chartly.core.execute_query import execute_query
from odoo.addons.chartly.core.query_to_plot import query_to_plot
from odoo.addons.chartly.core.nl_to_model import nl_to_model
from odoo.http import request
import json

from logging import getLogger
logger = getLogger(__name__)

# global, lazily evaluated
_openai_client_override = None
_env = None

def _get_env():
    logger.info(f"_env override: {_env}")
    return _env or request.env

def _get_openai_client():
    return _openai_client_override or get_openai_client(_get_env())

def query_returning_text(text: str):
    pass

def query_returning_plot(query:str):

    odoo_env = _get_env()
    openai_client = _get_openai_client()

    # Get Odoo model
    nl_to_model_response = nl_to_model(openai_client, query)
    models = nl_to_model_response.get("models")
    logger.info(f"NL to Model response: Model: {models}")

    # NL to Query safety checks
    if nl_to_model_response.get("not_restricted"):
        message = "Chartly only support integration with Invoicing/Accounting apps. Your query requires integration with other apps."
        logger.info(message) 
        return message
    
    if len(models) > 1:
        message = "Chartly only supports queries on a single Odoo model at a time. Please rephrase your query."
        logger.info(message)
        return message
    
    model = models[0]

    # Get Odoo domain from natural language
    nl_to_domain_response = nl_to_domain(openai_client, query, model, get_model_fields(model))
    domain = nl_to_domain_response.get("domain")

    if nl_to_domain_response.get("not_safe"):
        message = "Your query contains unsafe operations that are not allowed."
        logger.info(message)
        return message
    
    if nl_to_domain_response.get("not_formatted"):
        message = "Can you please rephrase your query? We were unable to understand it."
        logger.info(message)
        return message
    
    logger.info(f"NL to Domain response: Model: {model}, Domain: {domain}")
    
    # Execute the query to get data
    raw_data = execute_query(odoo_env, model, domain)
    
    # Get attributes from data and filter them
    attributes = raw_data[0].keys()
    attributes = filter_attributes(openai_client, query, model, attributes)
    
    # Retain relevant attributes using filtering
    filtered_data = []
    for record in raw_data:
        filtered_record = {attr: record[attr] for attr in attributes}
        filtered_data.append(filtered_record)

    # Generate plot from filtered data
    plot_script = query_to_plot(openai_client, query, attributes)

    # Extract the script function and execute it to get the plot
    plot_function = extract_script_as_fct(plot_script, "build_plot")
    plot_binary = plot_function(filtered_data)

    return plot_binary
    