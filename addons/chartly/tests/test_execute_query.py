from odoo.tests.common import TransactionCase
from odoo.addons.chartly.core.execute_query import execute_query
from logging import getLogger

logger = getLogger(__name__)

class TestExecuteQuery(TransactionCase):

    def setUp(self):
        super().setUp()

        # Create test partners
        self.partner_1 = self.env['res.partner'].create({
            'name': 'Test Partner 1',
            'email': 'partner1@example.com'
        })
        self.partner_2 = self.env['res.partner'].create({
            'name': 'Test Partner 2',
            'email': 'partner2@example.com'
        })
        self.partner_3 = self.env['res.partner'].create({
            'name': 'Test Partner 3',
            'email': 'partner3@example.com'
        })

    def test_execute_query_single_result(self):
        domain = "[('name', '=', 'Test Partner 1')]"
        result = execute_query(self.env, 'res.partner', domain)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Test Partner 1')
        # logger.info(f"Test results: {result}")

    def test_execute_query_multiple_results(self):
        domain = "[('name', 'in', ['Test Partner 1', 'Test Partner 2'])]"
        result = execute_query(self.env,'res.partner', domain)
        self.assertEqual(len(result), 2)
        names = [r['name'] for r in result]
        self.assertIn('Test Partner 1', names)
        self.assertIn('Test Partner 2', names)

    def test_execute_query_all_results(self):
        domain = "[]"
        result = execute_query(self.env,'res.partner', domain)
        self.assertTrue(len(result) >= 3)

    def test_execute_query_no_results(self):
        domain = "[('name', '=', 'Nonexistent')]"
        result = execute_query(self.env,'res.partner', domain)
        self.assertEqual(result, [])

    def test_execute_query_invalid_domain(self):
        domain = "invalid_domain"
        result = execute_query(self.env,'res.partner', domain)
        self.assertEqual(result, [])
