import base64
from odoo.addons.chartly.core.utils import get_model_fields
from odoo.addons.chartly.core.utils import extract_script_as_fct
from odoo.addons.chartly.core.openai import get_openai_client, create_function_tool
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

    if not raw_data:
        return [], cost, sql_query

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

    return filtered_data, cost, sql_query

def query_returning_text(query: str, limit: int = 10):
    cost=0
    try:
        openai_client = _get_openai_client()
        odoo_env = _get_env()

        filtered_data, cost, _ = _get_data(openai_client, odoo_env, query)

        if not filtered_data:
            return {"text": "No records", "cost": cost}

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
    except Exception as e:
        logger.error(f"Error executing tool {e}")
        return {"text": "Error executing tool", "cost": cost}
        
    return {"text": "\n".join(result_lines), "cost": cost}

def query_returning_plot(query:str):
    cost= 0
    try:
        openai_client = _get_openai_client()
        odoo_env = _get_env()

        filtered_data, cost, sql_query = _get_data(openai_client, odoo_env, query)

        if not filtered_data:
            return {"text": "No records", "cost": cost}

        attributes = list(filtered_data[0].keys())

        # Generate plot from filtered data
        response = query_to_plot(openai_client, query, sql_query)
        plot_script = response.get("plot_script")
        cost += response.get("cost", 0)

        # Extract the script function and execute it to get the plot
        plot_function = extract_script_as_fct(plot_script, "build_plot")
        plot_as_base64 = plot_function(filtered_data)
    except Exception as e:
        logger.error(f"Error executing tool {e}")
        return {"text": "Error executing tool", "cost": cost}

    return {"text": "Plot generated successfully", "image": plot_as_base64,  "cost": cost}

def get_tools():
    
    plot_tool = create_function_tool(
            name="query_returning_plot",
            description="Generates a plot image based on the provided natural language query.",
            parameters= {
                "query": {
                    "type": "string",
                    "description": "The natural language query describing the plot to generate."
                }
            }, 
            required=["query"]
        )
    
    retrieve_tool = create_function_tool(
            name="query_returning_text",
            description="Executes a natural language query and returns the results as text.",
            parameters= {
                "query": {
                    "type": "string",
                    "description": "The natural language query to execute against the database."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return."
                }
            }, 
            required=["query"]
        )
    
    tools_descriptions = [plot_tool, retrieve_tool]

    tools_map = {
            "query_returning_text": {
                "return_type": "text",
                "tool_callable": query_returning_text,
            },
            "query_returning_plot": {
                "return_type": "image",
                "tool_callable": query_returning_plot,
            }
        }
    
    return tools_map, tools_descriptions
    