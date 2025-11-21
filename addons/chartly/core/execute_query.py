from odoo.addons.chartly.core.utils import parse_odoo_domain

from logging import getLogger
logger = getLogger(__name__)

def execute_query(env, model: str, domain: str) -> list:
    try:
        domain = parse_odoo_domain(domain)
        logger.info(f"Executing query on model: {model} with domain: {domain}")
        records = env[model].search(domain)
        result = []
        for rec in records:
            result.append(rec.read()[0])
        logger.info(f"Query returned {len(result)} records.")
        return result
    except Exception as e:
        logger.error(f"Error executing query on model: {model} - Error: {e}")
        return []
