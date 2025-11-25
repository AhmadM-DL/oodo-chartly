from odoo.tests.common import TransactionCase
from odoo.addons.chartly.core.openai import OpenAIClient
from odoo.addons.chartly.core.utils import get_model_fields
from odoo.addons.chartly.core.nl_to_sql import nl_to_sql
import os

from logging import getLogger
logger = getLogger(__name__)

class TestOpenAIClientLive(TransactionCase):

    def setUp(self):
        super().setUp()
        self.api_key_file = os.environ.get("OPENAI_API_KEY_FILE")
        with open(self.api_key_file, "r") as f:
            self.api_key = f.read()
        self.model = os.environ.get("OPENAI_MODEL")
        self.client = OpenAIClient(self.api_key, self.model)

    def test_nl_to_sql(self):
        query = "List all invoices over 1000 USD created in the last month"
        models = ["account.move"]
        fields = {m: get_model_fields(m) for m in models}
        sql_query = nl_to_sql(self.client, query, models, fields)
        logger.info(f"NL to SQL: {sql_query}")
        self.assertIn("SELECT", sql_query.upper())
        self.assertIn("FROM", sql_query.upper())

    