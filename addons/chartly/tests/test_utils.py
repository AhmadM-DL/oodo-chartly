from odoo.tests.common import TransactionCase
from odoo.addons.chartly.core.utils import extract_script_as_fct

class TestSafeDomainEval(TransactionCase):

    def test_script_extraction(self):
        script = """
def calculate(a, b):
    return a + b
        """
        func = extract_script_as_fct(script, "calculate")
        result = func(2, 3)
        self.assertEqual(result, 5)