import base64
from odoo.addons.chartly.core.utils import get_model_fields
from odoo.addons.chartly.core.utils import extract_script_as_fct
from odoo.addons.chartly.core.openai import get_openai_client
from odoo.addons.chartly.core.filter_model_attributes import filter_attributes
from odoo.addons.chartly.core.nl_to_sql import nl_to_sql
from odoo.addons.chartly.core.execute_query import execute_query
from odoo.addons.chartly.core.query_to_plot import query_to_plot
from odoo.addons.chartly.core.nl_to_model import nl_to_model
from odoo.addons.chartly.core.utils import is_allowed_oodoo_model
import os
from odoo.http import request

from logging import getLogger
logger = getLogger(__name__)

# global, lazily evaluated
_openai_client_override = None
_env = None

PLOTS_DIR = "/tmp/chartly"

PLOT_TAG = "PLOT_666"

def _get_env():
    logger.info(f"_env override: {_env}")
    return _env or request.env

def _get_openai_client():
    return _openai_client_override or get_openai_client(_get_env())

def _get_data(openai_client, odoo_env, query: str):

    cost=0 

    # Get Odoo model
    response = nl_to_model(openai_client, query)
    models = response.get("models")
    cost += response.get("cost", 0)
    logger.info(f"NL to Model response: Model: {models}, Cost: {cost}")

    # NL to Query safety checks
    if not all(is_allowed_oodoo_model(m) for m in models):
        message = "Chartly only support integration with Invoicing/Accounting apps. Your query requires integration with other apps."
        logger.info(message) 
        return message

    # Get SQL from natural language
    fields = {m: get_model_fields(m) for m in models}
    response = nl_to_sql(openai_client, query, models, fields)
    sql_query = response.get("sql_query")
    cost += response.get("cost", 0)

    logger.info(f"NL to SQL response: Models: {models}, SQL Query: {sql_query}")
    
    # Execute the query to get data
    output = execute_query(odoo_env, sql_query)

    if output.get("not_safe"):
        message = "Your query contains unsafe operations that are not allowed."
        logger.info(message)
        return message
    
    if output.get("not_formatted"):
        message = "Can you please rephrase your query? We were unable to understand it."
        logger.info(message)
        return message
    
    raw_data = output.get("data")

    # Get attributes from data and filter them
    attributes = raw_data[0].keys()
    response = filter_attributes(openai_client, query, attributes)
    attributes = response.get("attributes")
    cost += response.get("cost", 0)
    
    # Retain relevant attributes using filtering
    filtered_data = []
    for record in raw_data:
        filtered_record = {attr: record[attr] for attr in attributes}
        filtered_data.append(filtered_record)

    return filtered_data, cost

def query_returning_text(query: str, limit: int = 10):

    openai_client = _get_openai_client()
    odoo_env = _get_env()

    filtered_data, cost = _get_data(openai_client, odoo_env, query)
    filtered_data = filtered_data[:limit]

    result_lines = []
    result_lines.append(f"**Found {len(filtered_data)} record(s):**\n")

    for i, record in enumerate(filtered_data):
        result_lines.append(f"**{i}.**")
        for key, value in record.items():
            field_name = key.replace('_', ' ').title()
            display_value = value if value is not None else 'N/A'
            result_lines.append(f"  • {field_name}: {display_value}")
        result_lines.append("")
    
    if len(filtered_data) > limit:
        result_lines.append(f"\n*... and {len(filtered_data) - limit} more record(s)*")
    
    return {"text": "\n".join(result_lines), "cost": cost}

def query_returning_plot(query:str):
    
    openai_client = _get_openai_client()
    odoo_env = _get_env()

    filtered_data, cost = _get_data(openai_client, odoo_env, query)

    attributes = list(filtered_data[0].keys())

    # Generate plot from filtered data
    response = query_to_plot(openai_client, query, attributes)
    plot_script = response.get("plot_script")
    cost += response.get("cost", 0)

    # Extract the script function and execute it to get the plot
    plot_function = extract_script_as_fct(plot_script, "build_plot")
    plot_as_base64 = plot_function(filtered_data)

    # write to temp file for manual verification
    uuid = os.urandom(4).hex()
    img_filepath = os.path.join(PLOTS_DIR, f"{uuid}.png")
    os.makedirs(os.path.dirname(img_filepath), exist_ok=True)
    with open(img_filepath, "wb") as f:
        f.write(base64.b64decode(plot_as_base64))

    return {"text": f"Plot generated successfully.<{PLOT_TAG}:{uuid}>", "cost": cost}
    