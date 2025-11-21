import ast

def execute_query(env, model: str, domain: str) -> list:
    try:
        domain = ast.literal_eval(domain)
        records = env[model].search(domain)
        result = []
        for rec in records:
            result.append(rec.read()[0])
        return result
    except Exception as e:
        return []
