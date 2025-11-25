import re
import sqlvalidator
from logging import getLogger
logger = getLogger(__name__)

def is_formatted(query: str) -> bool:
    try:
        validation = sqlvalidator.parse(query)
        return validation.is_valid()
    except Exception as e:
        logger.error(f"Error during SQL validation: {e}")
        return False

def is_safe(query: str) -> bool:
    sql = query.strip().lower()

    if not sql.startswith("select"):
        return False

    forbidden_commands = [
        r"\binsert\b", r"\bupdate\b", r"\bdelete\b",
        r"\bdrop\b", r"\bcreate\b", r"\balter\b",
        r"\btruncate\b", r"\bgrant\b", r"\brevoke\b",
        r"\breplace\b", r"\bcommit\b", r"\brollback\b"
    ]

    forbidden_code = [
        "__import__", "eval", "exec", "sudo", "env[", ".env"
    ]

    for pattern in forbidden_commands:
        if re.search(pattern, sql):
            return False

    for keyword in forbidden_code:
        if keyword in sql:
            return False

    return True


def execute_query(env, sql_query: str) -> dict:
    resutls = {}
    
    logger.info("Validating SQL query safety.")
    
    if not is_safe(sql_query):
        logger.warning(f"Unsafe SQL query detected: {sql_query}")
        resutls["not_safe"] = True
        resutls["data"] = []
        return resutls
    
    if not is_formatted(sql_query):
        logger.warning(f"Malformed SQL query detected: {sql_query}")
        resutls["not_formatted"] = True
        resutls["data"] = []
        return resutls
        
    try:
        logger.info(f"Executing SQL query: {sql_query}")
        env.cr.execute(sql_query)
        columns = [desc[0] for desc in env.cr.description]
        rows = env.cr.fetchall()
        logger.info(f"Query returned {len(rows)} records.")
        resutls["data"] = [dict(zip(columns, row)) for row in rows]
        return resutls
    
    except Exception as e:
        logger.error(f"Error executing query: {sql_query} - Error: {e}")
        resutls["error"] = str(e)
        resutls["data"] = []
        return resutls