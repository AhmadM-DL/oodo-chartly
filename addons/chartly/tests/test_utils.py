from odoo.tests.common import TransactionCase
from odoo.addons.chartly.core.utils import parse_odoo_domain

class TestSafeDomainEval(TransactionCase):

    def test_valid_domain(self):
        domain = """[
            ('name', '=', 'Ahmad'),
            ('invoice_date', '>=', datetime.date.today() - datetime.timedelta(days=30))
        ]"""
        result = parse_odoo_domain(domain)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0][0], "name")

    def test_reject_unknown_function(self):
        domain = "[('name', '=', badfunc('x'))]"
        with self.assertRaises(ValueError):
            parse_odoo_domain(domain)

    def test_reject_import(self):
        domain = "[('name', '=', __import__('os').system('rm -rf /'))]"
        with self.assertRaises(ValueError):
            parse_odoo_domain(domain)

    def test_reject_attributes_not_allowed(self):
        domain = "[('date', '=', os.path.join('a','b'))]"
        with self.assertRaises(ValueError):
            parse_odoo_domain(domain)
