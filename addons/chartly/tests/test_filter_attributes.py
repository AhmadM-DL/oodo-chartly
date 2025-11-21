from odoo.tests.common import TransactionCase
from odoo.addons.chartly.core.openai import OpenAIClient
from odoo.addons.chartly.core.filter_model_attributes import filter_attributes
import os

from logging import getLogger
logger = getLogger(__name__)

class TestOpenAIClientLive(TransactionCase):

    def setUp(self):
        super().setUp()
        self.api_key_file = os.environ.get("OPENAI_API_KEY_FILE")
        with open(self.api_key_file, "r") as f:
            self.api_key = f.read()
        self.client = OpenAIClient(self.api_key)

        self.partner_1 = self.env['res.partner'].create({
            'name': 'Test Partner 1',
            'email': 'partner1@example.com'
        })

    def test_filter_attributes(self):
        query = "List all customers"
        model = "res.partner"
        domain = [("customer_rank", ">", 0)]
        env = self.env
        records = env[model].search(domain)
        attributes = records[0]._fields.keys()
        logger.info(f"All attributes: {attributes}")
        content = filter_attributes(self.client, query, model, attributes)
        logger.info(f"Filtered attributes: {content}")
