"""Test script for execute_query.py with REAL Odoo environment"""

import sys
import odoo
from odoo import api, SUPERUSER_ID


def test_execute_query_real():
    """Test the query executor with REAL Odoo data"""
    
    # Get database name from config
    db_name = odoo.tools.config['db_name']
    print(f"\n✅ Using REAL Odoo Database: {db_name}")
    
    # Create environment
    registry = odoo.registry(db_name)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Import execute_query module
        from execute_query import OdooQueryExecutor
        
        # Create executor
        executor = OdooQueryExecutor(env)
        
        print("\n" + "="*80)
        print("ODOO DOMAIN QUERY EXECUTOR - REAL DATA TEST RESULTS")
        print("="*80)
        
        # Test cases based on actual invoice data (REDUCED for efficiency)
        test_cases = [
            {
                'name': 'All Posted Invoices',
                'model': 'account.move',
                'domain': [('move_type', '=', 'out_invoice'), ('state', '=', 'posted')],
                'description': 'Get all posted customer invoices'
            },
            {
                'name': 'Not Paid Invoices',
                'model': 'account.move',
                'domain': [('payment_state', '=', 'not_paid'), ('state', '=', 'posted')],
                'description': 'Get all unpaid invoices'
            },
            {
                'name': 'All Customers',
                'model': 'res.partner',
                'domain': [('customer_rank', '>', 0)],
                'description': 'Get all customers'
            },
            {
                'name': 'Products with Low Stock',
                'model': 'product.product',
                'domain': [('qty_available', '<', 10), ('type', '=', 'product')],
                'description': 'Get products with quantity less than 10'
            },
            {
                'name': 'Posted Payments',
                'model': 'account.payment',
                'domain': [('state', '=', 'posted'), ('payment_type', '=', 'inbound')],
                'description': 'Get all posted inbound payments'
            }
        ]
        
        passed = 0
        failed = 0
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n{'─'*80}")
            print(f"Test {i}/{len(test_cases)}: {test['name']}")
            print(f"{'─'*80}")
            print(f"Description: {test['description']}")
            print(f"Model: {test['model']}")
            print(f"Domain: {test['domain']}")
            
            try:
                # Execute query on REAL Odoo data
                result = executor.execute_and_format(test['model'], test['domain'], limit=10)
                
                if result['success']:
                    print(f"\n✅ Status: SUCCESS")
                    print(f"Records Found: {result['count']}")
                    
                    # Show summary if available
                    if 'summary' in result:
                        print(f"\nSummary:")
                        for key, value in result['summary'].items():
                            if isinstance(value, dict):
                                print(f"  {key}:")
                                for k, v in value.items():
                                    print(f"    - {k}: {v}")
                            else:
                                print(f"  {key}: {value}")
                    
                    # Show first record with FULL DATA for first test
                    if result['records'] and i == 1:
                        print(f"\n📋 FULL RAW OUTPUT FOR FIRST TEST:")
                        import json
                        print(json.dumps(result, indent=2, default=str))
                    elif result['records']:
                        print(f"\nSample Record (first one):")
                        record = result['records'][0]
                        for key, value in list(record.items())[:8]:  # Show first 8 fields
                            if isinstance(value, dict) and 'name' in value:
                                print(f"  {key}: {value['name']}")
                            elif isinstance(value, (int, float, str, bool, type(None))):
                                print(f"  {key}: {value}")
                    
                    passed += 1
                else:
                    print(f"\n❌ Status: FAILED")
                    print(f"Error: {result.get('error', 'Unknown error')}")
                    failed += 1
                    
            except Exception as e:
                print(f"\n❌ Status: EXCEPTION")
                print(f"Error: {str(e)}")
                import traceback
                traceback.print_exc()
                failed += 1
        
        # Summary
        total = len(test_cases)
        print(f"\n{'='*80}")
        print(f"TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total Tests: {total}")
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failed}")
        print(f"\n🎯 Success Rate: {(passed/total)*100:.1f}%")
        print(f"{'='*80}\n")
        
        return passed == total


if __name__ == '__main__':
    print("\n🚀 Starting Odoo Domain Query Executor Tests (REAL DATA)...\n")
    
    try:
        success = test_execute_query_real()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
