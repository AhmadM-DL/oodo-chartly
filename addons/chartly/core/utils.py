import os
import json

from logging import getLogger
logger = getLogger(__name__)


ALLOWED_ODOO_MODELS_FILENAME = "allowed_odoo_models.txt"
MODEL_FIELDS_MAP_FILE = "accounting_schema.json"
    
def extract_script_as_fct(script: str, function_name: str = "build_plot"):
    namespace = {}
    exec(script, namespace)
    return namespace[function_name]

def is_allowed_oodoo_model(model: str) -> bool:
    allowed_models_file = os.path.join(os.path.dirname(__file__), ALLOWED_ODOO_MODELS_FILENAME)
    with open(allowed_models_file, "r") as f:
        allowed_models = f.read().split()
    return model in allowed_models

def get_model_fields(model: str) -> list:
    model_fields_map_file = os.path.join(os.path.dirname(__file__), MODEL_FIELDS_MAP_FILE)
    logger.info(f"Loading model fields from: {model_fields_map_file}")
    model_fields_map = json.load(open(model_fields_map_file, "r"))
    logger.info(f"Loaded fields for {len(model_fields_map.keys())} models")
    model = model.replace('.', '_')
    return model_fields_map.get(model, [])
