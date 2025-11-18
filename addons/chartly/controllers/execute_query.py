"""Execute Odoo Domain Queries on Invoicing Models"""

import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class OdooQueryExecutor:
    """Executes domain queries on Odoo models and returns formatted data"""
    
    def __init__(self, env):
        """
        Initialize the query executor with Odoo environment
        
        :param env: Odoo environment object
        """
        self.env = env
    
    def execute(self, model_name, domain, limit=50, fields=None, order=None):
        """
        Execute a domain query on an Odoo model
        
        :param model_name: Odoo model name (e.g., 'account.move', 'res.partner')
        :param domain: Odoo domain filter as list of tuples
        :param limit: Maximum number of records to return (default: 50)
        :param fields: List of field names to retrieve (default: None = all fields)
        :param order: Sort order (e.g., 'name asc', 'create_date desc')
        :return: List of dictionaries containing record data
        """
        try:
            # Validate model exists
            if model_name not in self.env:
                raise ValueError(f"Model '{model_name}' not found in environment")
            
            # Get the model
            model = self.env[model_name]
            
            # Execute search
            records = model.search(domain, limit=limit, order=order)
            
            _logger.info(f"Found {len(records)} records for model '{model_name}' with domain {domain}")
            
            # If no specific fields requested, use a smart default set
            if fields is None:
                fields = self._get_default_fields(model_name)
            
            # Convert records to dictionaries
            result = []
            for record in records:
                record_data = {}
                for field in fields:
                    if hasattr(record, field):
                        value = getattr(record, field)
                        # Handle special field types
                        record_data[field] = self._format_field_value(value)
                    else:
                        _logger.warning(f"Field '{field}' not found in model '{model_name}'")
                
                result.append(record_data)
            
            return {
                'success': True,
                'model': model_name,
                'count': len(result),
                'records': result
            }
            
        except Exception as e:
            _logger.error(f"Error executing query on '{model_name}': {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'model': model_name,
                'count': 0,
                'records': []
            }
    
    def _get_default_fields(self, model_name):
        """
        Get default fields to retrieve based on model type
        
        :param model_name: Odoo model name
        :return: List of field names
        """
        # Default field sets for common invoicing models
        field_mappings = {
            'account.move': [
                'id', 'name', 'move_type', 'partner_id', 'invoice_date', 
                'invoice_date_due', 'state', 'payment_state', 'amount_total',
                'amount_untaxed', 'amount_tax', 'currency_id'
            ],
            'res.partner': [
                'id', 'name', 'email', 'phone', 'street', 'city', 'zip',
                'country_id', 'is_company', 'customer_rank', 'supplier_rank'
            ],
            'product.product': [
                'id', 'name', 'default_code', 'list_price', 'standard_price',
                'type', 'qty_available', 'categ_id', 'uom_id'
            ],
            'account.payment': [
                'id', 'name', 'partner_id', 'amount', 'payment_date',
                'state', 'payment_type', 'partner_type', 'currency_id'
            ],
            'account.move.line': [
                'id', 'move_id', 'name', 'account_id', 'partner_id',
                'debit', 'credit', 'balance', 'date'
            ],
            'account.journal': [
                'id', 'name', 'code', 'type', 'currency_id', 'active'
            ],
            'account.tax': [
                'id', 'name', 'amount', 'type_tax_use', 'amount_type', 'active'
            ]
        }
        
        # Return specific fields if mapped, otherwise generic fields
        return field_mappings.get(model_name, ['id', 'name', 'display_name'])
    
    def _format_field_value(self, value):
        """
        Format field value for JSON serialization
        
        :param value: Field value from Odoo record
        :return: Formatted value
        """
        # Handle Many2one fields (returns tuple of (id, name))
        if hasattr(value, 'name') and hasattr(value, 'id'):
            return {'id': value.id, 'name': value.name}
        
        # Handle One2many and Many2many fields
        elif hasattr(value, '__iter__') and hasattr(value, 'ids'):
            return [{'id': r.id, 'name': r.display_name} for r in value]
        
        # Handle datetime objects
        elif isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        
        # Handle date objects
        elif hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        
        # Handle boolean, string, int, float
        else:
            return value
    
    def execute_and_format(self, model_name, domain, limit=50):
        """
        Execute query and return formatted, human-readable results
        
        :param model_name: Odoo model name
        :param domain: Odoo domain filter
        :param limit: Maximum number of records
        :return: Dictionary with formatted results
        """
        result = self.execute(model_name, domain, limit=limit)
        
        if not result['success']:
            return result
        
        # Add summary information
        result['summary'] = self._generate_summary(model_name, result['records'])
        
        return result
    
    def _generate_summary(self, model_name, records):
        """
        Generate summary statistics for the query results
        
        :param model_name: Odoo model name
        :param records: List of record dictionaries
        :return: Summary dictionary
        """
        if not records:
            return {'total_records': 0}
        
        summary = {'total_records': len(records)}
        
        # Model-specific summaries
        if model_name == 'account.move':
            # Sum totals for invoices
            total_amount = sum(r.get('amount_total', 0) for r in records)
            summary['total_amount'] = total_amount
            
            # Count by state
            states = {}
            for r in records:
                state = r.get('state', 'unknown')
                states[state] = states.get(state, 0) + 1
            summary['by_state'] = states
            
            # Count by payment state
            payment_states = {}
            for r in records:
                pstate = r.get('payment_state', 'unknown')
                payment_states[pstate] = payment_states.get(pstate, 0) + 1
            summary['by_payment_state'] = payment_states
        
        elif model_name == 'res.partner':
            # Count customers vs suppliers
            customers = sum(1 for r in records if r.get('customer_rank', 0) > 0)
            suppliers = sum(1 for r in records if r.get('supplier_rank', 0) > 0)
            summary['customers'] = customers
            summary['suppliers'] = suppliers
        
        elif model_name == 'account.payment':
            # Sum payment amounts
            total_amount = sum(r.get('amount', 0) for r in records)
            summary['total_amount'] = total_amount
            
            # Count by payment type
            payment_types = {}
            for r in records:
                ptype = r.get('payment_type', 'unknown')
                payment_types[ptype] = payment_types.get(ptype, 0) + 1
            summary['by_payment_type'] = payment_types
        
        return summary


def get_query_executor():
    """
    Factory function to create OdooQueryExecutor with current environment
    
    :return: OdooQueryExecutor instance
    """
    try:
        from odoo.http import request
        
        if hasattr(request, 'env'):
            return OdooQueryExecutor(request.env)
        else:
            raise Exception("No Odoo environment available in request context")
            
    except Exception as e:
        _logger.error(f"Error creating query executor: {str(e)}")
        raise


def execute_domain_query(model_name, domain, limit=50):
    """
    Main function to execute a domain query
    
    :param model_name: Odoo model name
    :param domain: Odoo domain filter as list of tuples
    :param limit: Maximum records to return
    :return: Query results dictionary
    """
    executor = get_query_executor()
    return executor.execute_and_format(model_name, domain, limit)
