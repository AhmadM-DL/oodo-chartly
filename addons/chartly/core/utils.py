import ast
import datetime
import time

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
    }

    try:
        tree = ast.parse(domain_str, mode='eval')
        code = compile(tree, "<domain>", mode="eval")
        evaluated = eval(code, safe_globals, {})
        evaluated = make_hashable(evaluated)
        return evaluated

    except Exception as e:
        raise ValueError(f"Invalid domain: {domain_str}\nError: {e}")
