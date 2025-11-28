import os
import re
import ast
import json

from logging import getLogger
logger = getLogger(__name__)


ALLOWED_ODOO_MODELS_FILENAME = "allowed_odoo_models.txt"
MODEL_FIELDS_MAP_FILE = "accounting_schema.json"


def is_valid_python(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        logger.error(f"Syntax error in generated code: {e}")
        return False


def is_safe_code(code: str) -> bool:

    forbidden_imports = [
        r"\bimport\s+os\b",
        r"\bimport\s+sys\b",
        r"\bimport\s+subprocess\b",
        r"\bimport\s+shutil\b",
        r"\bimport\s+socket\b",
        r"\bimport\s+requests\b",
        r"\bimport\s+urllib\b",
        r"\bfrom\s+os\b",
        r"\bfrom\s+sys\b",
        r"\bfrom\s+subprocess\b",
    ]

    forbidden_functions = [
        r"\beval\s*\(",
        r"\bexec\s*\(",
        r"\bcompile\s*\(",
        r"\bopen\s*\(",
        r"\b__import__\s*\(",
        r"\bgetattr\s*\(",
        r"\bsetattr\s*\(",
        r"\bglobals\s*\(",
        r"\blocals\s*\(",
    ]

    forbidden_attributes = [
        "__builtins__", "__class__", "__bases__",
        "__subclasses__", "__mro__", "__code__",
        "__globals__", "__dict__"
    ]

    forbidden_system = [
        r"\.system\s*\(",
        r"\.popen\s*\(",
        r"\.spawn",
        r"\.call\s*\(",
        r"\.Popen\s*\(",
    ]

    for pattern in forbidden_imports:
        if re.search(pattern, code, re.IGNORECASE):
            logger.warning(f"Forbidden import detected: {pattern}")
            return False

    for pattern in forbidden_functions:
        if re.search(pattern, code, re.IGNORECASE):
            logger.warning(f"Forbidden function detected: {pattern}")
            return False

    for attr in forbidden_attributes:
        if attr in code:
            logger.warning(f"Forbidden attribute detected: {attr}")
            return False

    for pattern in forbidden_system:
        if re.search(pattern, code, re.IGNORECASE):
            logger.warning(f"Forbidden system call detected: {pattern}")
            return False

    return True


def clean_code_block(code: str) -> str:
    code = code.strip()
    if code.startswith("```python"):
        code = code[9:]
    elif code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    return code.strip()


def extract_script_as_fct(script: str, function_name: str = "build_plot"):
    script = clean_code_block(script)
    
    if not is_safe_code(script):
        raise ValueError("Unsafe code detected")
    
    if not is_valid_python(script):
        raise ValueError("Invalid Python syntax")
    
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import base64
    from io import BytesIO
    
    namespace = {
        'plt': plt,
        'matplotlib': matplotlib,
        'base64': base64,
        'BytesIO': BytesIO,
    }
    
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
