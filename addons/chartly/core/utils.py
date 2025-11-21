import ast
import datetime
from dateutil.relativedelta import relativedelta
import os
import time
import json

from logging import getLogger
logger = getLogger(__name__)

MODLE_FIELDS_MAP_FILE = "accounting_schema.json"

def make_hashable(domain):
    new_domain = []
    for cond in domain:
        field, op, value = cond
        if isinstance(value, list):
            value = tuple(value)
        new_domain.append((field, op, value))
    return new_domain

def parse_odoo_domain(domain_str: str):
    """
    Safely parse an Odoo domain string into a Python object.
    Supports datetime, timedelta, and blocks dangerous imports.
    """

    # Safe import override allowing only datetime + time
    def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "datetime":
            return datetime
        if name == "time":
            return time
        raise ImportError(f"Import of '{name}' not allowed")

    safe_globals = {
        "__builtins__": {
            "__import__": safe_import
        },
        "datetime": datetime,
        "time": time,                         # required by datetime internals
        "timedelta": datetime.timedelta,
        'relativedelta': relativedelta,
    }

    try:
        tree = ast.parse(domain_str, mode='eval')
        code = compile(tree, "<domain>", mode="eval")
        evaluated = eval(code, safe_globals, {})
        evaluated = make_hashable(evaluated)
        return evaluated

    except Exception as e:
        raise ValueError(f"Invalid domain: {domain_str} - Error: {e}")
    
def extract_script_as_fct(script: str, function_name: str = "build_plot"):
    namespace = {}
    exec(script, namespace)
    return namespace[function_name]

def get_model_fields(model: str) -> list:
    model_fields_map_file = os.path.join(os.path.dirname(__file__), MODLE_FIELDS_MAP_FILE)
    logger.info(f"Loading model fields from: {model_fields_map_file}")
    model_fields_map = json.load(open(model_fields_map_file, "r"))
    logger.info(f"Loaded fields for {len(model_fields_map.keys())} models")
    model = model.replace('.', '_')
    return model_fields_map.get(model, [])
