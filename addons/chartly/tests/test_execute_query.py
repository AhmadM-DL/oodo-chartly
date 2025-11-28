from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.addons.chartly.core.execute_query import execute_query

@tagged('unit', 'execute_query')
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

    # -----------------------------
    # ✔ Test safe SELECT
    # -----------------------------
    def test_safe_select_query(self):
        sql = "SELECT name, email FROM res_partner WHERE name LIKE 'Test Partner%';"
        result = execute_query(self.env, sql)
        self.assertFalse(result.get("not_safe", False))
        self.assertFalse(result.get("not_formatted", False))
        self.assertTrue(isinstance(result.get("data"), list))
        self.assertTrue(len(result["data"]) >= 3)
        self.assertIn("name", result["data"][0])
        self.assertIn("email", result["data"][0])

    # -----------------------------
    # ✔ Test unsafe query (DROP)
    # -----------------------------
    def test_unsafe_drop_query(self):
        sql = "SELECT id FROM res_partner; DROP TABLE res_partner;"
        result = execute_query(self.env, sql)
        self.assertTrue(result.get("not_safe", True))
        self.assertEqual(result.get("data"), [])

    # -----------------------------
    # ✔ Test unsafe DELETE
    # -----------------------------
    def test_unsafe_delete_query(self):
        sql = "DELETE FROM res_partner;"
        result = execute_query(self.env, sql)
        self.assertTrue(result.get("not_safe", True))
        self.assertEqual(result.get("data"), [])

    # -----------------------------
    # ✔ Test invalid SQL syntax
    # -----------------------------
    def test_invalid_sql_format(self):
        sql = "SELECT * FROM"
        result = execute_query(self.env, sql)
        self.assertTrue(result.get("not_formatted", True))
        self.assertEqual(result.get("data"), [])

    # -----------------------------
    # ✔ Test field names containing words like 'created_at'
    # -----------------------------
    def test_select_created_at_field(self):
        sql = "SELECT create_date FROM res_partner LIMIT 1;"
        result = execute_query(self.env, sql)
        self.assertFalse(result.get("not_safe", False))
        self.assertFalse(result.get("not_formatted", False))
        self.assertIsInstance(result.get("data"), list)

    # -----------------------------
    # ✔ Test safe query with upper/mixed case
    # -----------------------------
    def test_safe_mixed_case_select(self):
        sql = "SeLeCt name FROM res_partner;"
        result = execute_query(self.env, sql)
        self.assertFalse(result.get("not_safe", False))
        self.assertFalse(result.get("not_formatted", False))
        self.assertTrue(len(result.get("data")) > 0)

    # -----------------------------
    # ✔ Test code injection patterns (eval, env, exec)
    # -----------------------------
    def test_forbidden_code_injection(self):
        sql = "SELECT name FROM res_partner WHERE email LIKE '%exec(%';"
        result = execute_query(self.env, sql)
        self.assertTrue(result.get("not_safe", True))
        self.assertEqual(result.get("data"), [])

    # -----------------------------
    # ✔ Test SELECT with JOIN
    # -----------------------------
    def test_select_with_join(self):
        sql = """
        SELECT p.name, u.login
        FROM res_partner p
        JOIN res_users u ON u.partner_id = p.id
        LIMIT 5;
        """
        result = execute_query(self.env, sql)
        self.assertFalse(result.get("not_safe", False))
        self.assertFalse(result.get("not_formatted", False))
        self.assertIsInstance(result.get("data"), list)

    # -----------------------------
    # ✔ Test SELECT with ORDER BY
    # -----------------------------
    def test_select_with_order_by(self):
        sql = "SELECT name FROM res_partner ORDER BY name ASC;"
        result = execute_query(self.env, sql)
        self.assertFalse(result.get("not_safe", False))
        self.assertFalse(result.get("not_formatted", False))
        self.assertIsInstance(result.get("data"), list)

    # -----------------------------
    # ✔ Test SELECT with subquery
    # -----------------------------
    def test_select_with_subquery(self):
        sql = """
        SELECT name FROM res_partner
        WHERE id IN (SELECT id FROM res_partner WHERE email IS NOT NULL)
        """
        result = execute_query(self.env, sql)
        self.assertFalse(result.get("not_safe", False))
        self.assertFalse(result.get("not_formatted", False))
        self.assertIsInstance(result.get("data"), list)

    # -----------------------------
    # ✔ Test injection attempt using comment '--'
    # -----------------------------
    def test_comment_injection(self):
        sql = "SELECT name FROM res_partner WHERE name = 'Test' -- DROP TABLE res_partner;"
        result = execute_query(self.env, sql)
        self.assertTrue(result.get("not_safe", True))
        self.assertEqual(result.get("data"), [])
