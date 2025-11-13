"""Natural Language to Odoo Domain Query Converter using ChatGPT"""

import logging
import json
import re
from datetime import datetime, timedelta

try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    # Fallback for testing without dateutil
    relativedelta = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

_logger = logging.getLogger(__name__)


# Allowed Odoo models for invoicing/accounting domain
ALLOWED_MODELS = [
    "account.move",
    "account.move.line",
    "account.journal",
    "account.account",
    "account.group",
    "account.account.tag",
    "account.fiscal.position",
    "account.fiscal.position.tax",
    "account.fiscal.position.account",
    "account.tax",
    "account.tax.group",
    "account.tax.repartition.line",
    "account.payment",
    "account.payment.register",
    "account.payment.term",
    "account.payment.term.line",
    "account.bank.statement",
    "account.bank.statement.line",
    "account.reconcile.model",
    "res.partner",
    "res.partner.bank",
    "product.product",
    "product.template",
    "res.currency",
    "res.currency.rate",
    "account.analytic.account",
    "account.analytic.line",
    "account.asset",
    "account.asset.depreciation.line",
    "account.cash.rounding",
    "account.incoterms"
]


class NLToOdooDomain:
    """Converts natural language queries to Odoo domain filters using ChatGPT"""
    
    def __init__(self, api_key, allowed_models=None):
        """
        Initialize the converter with OpenAI API key
        
        :param api_key: OpenAI API key from settings
        :param allowed_models: List of allowed Odoo models (default: ALLOWED_MODELS)
        """
        if OpenAI is None:
            raise ImportError("OpenAI package is required. Install with: pip install openai")
        
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        self.allowed_models = allowed_models or ALLOWED_MODELS
    
    def convert(self, natural_language_query, model_name=None, limit=50):
        """
        Convert natural language to Odoo domain query with automatic model detection
        
        :param natural_language_query: User's natural language query
        :param model_name: Odoo model to query (optional, will be auto-detected if not provided)
        :param limit: Maximum number of records to return (default: 50)
        :return: Dict with keys: 'model', 'domain', 'limit'
        """
        try:
            # Step 1: Get structured response with model and domain
            system_prompt = self._get_system_prompt()
            user_prompt = self._format_user_prompt(natural_language_query, model_name)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            response_content = response.choices[0].message.content.strip()
            
            # Step 2: Parse JSON response
            parsed_response = self._parse_llm_response(response_content)
            
            # Step 3: Validate model is in allowed list
            detected_model = parsed_response['model']
            self._validate_model(detected_model)
            
            # Step 4: Validate domain is read-only
            domain_str = parsed_response['domain']
            self._validate_read_only(domain_str)
            
            result = {
                'model': detected_model,
                'domain': domain_str,
                'limit': limit
            }
            
            _logger.info(f"Converted '{natural_language_query}' to {result}")
            
            return result
            
        except Exception as e:
            _logger.error(f"Error converting natural language to domain: {str(e)}")
            raise Exception(f"Failed to convert query: {str(e)}")
    
    def _get_system_prompt(self):
        """Generate the system prompt for ChatGPT"""
        models_list = "\n".join([f"  - {model}" for model in self.allowed_models])
        
        return f"""You are an expert in Odoo ERP domain filters specialized in Accounting/Invoicing modules. Convert natural language queries into valid Odoo domain filters with automatic model detection.

🔒 CRITICAL SECURITY GUARDRAILS - MUST FOLLOW:
1. ONLY generate READ-ONLY domain filters for searching/filtering records
2. NEVER include fields or operations that modify, delete, or write data
3. NEVER use operators or fields that could trigger write/unlink operations
4. Only use safe read operators: '=', '!=', '>', '<', '>=', '<=', 'in', 'not in', 'like', 'ilike', '=like', '=ilike'
5. Domain filters are for SEARCH ONLY - no create, write, or delete operations allowed

🎯 ALLOWED MODELS ONLY:
You can ONLY use models from this invoicing/accounting domain:
{models_list}

If the user query references a model NOT in this list (e.g., hr.employee, stock.picking, crm.lead), you MUST respond with:
{{'Model': '...'
'Query': '...'}}

📊 RESPONSE FORMAT:
You MUST respond with a JSON object in this exact format:
{{
  "model": "account.move",
  "domain": "[('field', 'operator', value)]"
}}

Rules for model selection:
- "invoices" → account.move
- "customers/partners" → res.partner
- "products" → product.product
- "payments" → account.payment
- "journal entries/move lines" → account.move.line
- "journals" → account.journal
- "taxes" → account.tax
- "bank statements" → account.bank.statement

Odoo Domain Syntax Rules:
- Use Python list format: [('field', 'operator', value), ...]
- Common operators: '=', '!=', '>', '<', '>=', '<=', 'in', 'not in', 'like', 'ilike'
- Logical operators: '&' (AND), '|' (OR), '!' (NOT) - prefix notation
- Date handling: Use datetime objects or strings in 'YYYY-MM-DD' format

Key Model Fields:
- account.move: move_type, state, partner_id, invoice_date, amount_total, payment_state, journal_id
- res.partner: name, email, phone, country_id, is_company, customer_rank, supplier_rank
- product.product: name, list_price, categ_id, qty_available, standard_price
- account.payment: partner_id, amount, payment_date, state, payment_type
- account.move.line: move_id, account_id, debit, credit, balance, partner_id

Examples:
Query: "invoices from last month"
Response: {{"model": "account.move", "domain": "[('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_date', '>=', (datetime.date.today().replace(day=1) - timedelta(days=1)).replace(day=1)), ('invoice_date', '<', datetime.date.today().replace(day=1))]"}}

Query: "paid invoices"
Response: {{"model": "account.move", "domain": "[('move_type', '=', 'out_invoice'), ('payment_state', '=', 'paid')]"}}

Query: "customers from USA"
Response: {{"model": "res.partner", "domain": "[('country_id.code', '=', 'US'), ('customer_rank', '>', 0)]"}}

Query: "employees on leave" (NOT ALLOWED - hr.employee not in allowed models)
Response: {{"error": "Model not allowed. Only invoicing/accounting models are supported."}}

Return ONLY valid JSON. No markdown, no code blocks, no explanations."""

    def _format_user_prompt(self, query, model_name):
        """Format the user prompt with the query and model"""
        if model_name:
            return f"""Convert this natural language query to an Odoo domain filter.

Query: "{query}"
Model hint: {model_name}

Return JSON with "model" and "domain" fields. Use the model hint if provided, otherwise auto-detect from the query."""
        else:
            return f"""Convert this natural language query to an Odoo domain filter. Automatically detect the appropriate model.

Query: "{query}"

Return JSON with "model" and "domain" fields."""
    
    def _parse_llm_response(self, response_content):
        """
        Parse LLM response and extract model and domain
        
        :param response_content: Raw response from LLM
        :return: Dict with 'model' and 'domain' keys
        :raises Exception: If parsing fails or response contains error
        """
        # Clean up response - remove markdown code blocks if present
        cleaned = response_content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned.replace("```", "").strip()
        
        try:
            # Parse JSON response
            parsed = json.loads(cleaned)
            
            # Check for error response
            if 'error' in parsed:
                raise Exception(f"LLM Error: {parsed['error']}")
            
            # Check if response is in the disallowed model format: {'Model': '...', 'Query': '...'}
            if 'Model' in parsed and 'Query' in parsed:
                # This indicates a query for a disallowed model
                raise Exception(
                    f"Model not allowed. The query '{parsed.get('Query', 'N/A')}' references "
                    f"model '{parsed.get('Model', 'N/A')}' which is not in the invoicing/accounting domain. "
                    f"Only invoicing/accounting models are supported."
                )
            
            # Validate required fields for valid response
            if 'model' not in parsed or 'domain' not in parsed:
                raise Exception(
                    f"Invalid LLM response format. Expected JSON with 'model' and 'domain' fields. "
                    f"Got: {parsed}"
                )
            
            return {
                'model': parsed['model'],
                'domain': parsed['domain']
            }
            
        except json.JSONDecodeError as e:
            _logger.error(f"Failed to parse LLM response as JSON: {response_content}")
            raise Exception(f"Invalid JSON response from LLM: {str(e)}")
    
    def _validate_model(self, model_name):
        """
        Validate that the model is in the allowed list
        
        :param model_name: Model name to validate
        :raises Exception: If model is not allowed
        """
        if model_name not in self.allowed_models:
            raise Exception(
                f"Model '{model_name}' is not allowed. "
                f"Only invoicing/accounting models are supported. "
                f"Allowed models: {', '.join(self.allowed_models[:5])}..."
            )
    
    def _validate_read_only(self, domain_str):
        """
        Validate that the domain is read-only and doesn't contain dangerous operations
        
        :param domain_str: Domain string to validate
        :raises Exception: If domain contains potentially dangerous operations
        """
        # List of forbidden keywords that might indicate write/delete operations
        forbidden_keywords = [
            'write', 'unlink', 'create', 'delete', 'remove',
            'execute', 'sudo', 'env[', '.env', 'cr.execute',
            'commit', 'rollback', '__import__', 'eval', 'exec'
        ]
        
        domain_lower = domain_str.lower()
        
        for keyword in forbidden_keywords:
            if keyword in domain_lower:
                raise Exception(
                    f"Security violation: Domain contains forbidden keyword '{keyword}'. "
                    "Only read-only search operations are allowed."
                )
        
        # Additional check: domain should start with '[' and end with ']'
        if not (domain_str.strip().startswith('[') and domain_str.strip().endswith(']')):
            raise Exception(
                "Invalid domain format: Domain must be a Python list starting with '[' and ending with ']'"
            )


def get_nl_to_domain_converter():
    """
    Factory function to create NLToOdooDomain instance with API key from settings
    
    :return: NLToOdooDomain instance
    """
    from odoo import api, SUPERUSER_ID
    from odoo.http import request
    
    try:
        # Try to get from current environment
        if hasattr(request, 'env'):
            env = request.env
        else:
            # Fallback for testing
            import odoo
            env = api.Environment(odoo.registry(odoo.tools.config['db_name']), SUPERUSER_ID, {})
        
        api_key = env['ir.config_parameter'].sudo().get_param('chartly.openai_api_key')
        
        if not api_key:
            raise Exception("OpenAI API key not configured. Please set it in Settings.")
        
        return NLToOdooDomain(api_key)
        
    except Exception as e:
        _logger.error(f"Error initializing NL to Domain converter: {str(e)}")
        raise


def convert_nl_to_domain(natural_language_query, model_name=None):
    """
    Main function to convert natural language to Odoo domain with auto model detection
    
    :param natural_language_query: User's natural language query
    :param model_name: Odoo model to query (optional, auto-detected if not provided)
    :return: Dict with 'model', 'domain', 'limit' keys
    """
    converter = get_nl_to_domain_converter()
    return converter.convert(natural_language_query, model_name)
