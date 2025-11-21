from odoo.tests.common import TransactionCase
from odoo.addons.chartly.core.openai import OpenAIClient
from odoo.addons.chartly.core import tools
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
import os

from logging import getLogger
logger = getLogger(__name__)

class TestOpenAIClientLive(TransactionCase):

    def override_openai_client(self, client):
        tools._openai_client_override = client

    def override_env(self, env):
        tools._env = env

    def setUp(self):
        super().setUp()

        # ------------------------------
        # Load API key
        # ------------------------------
        self.api_key_file = os.environ.get("OPENAI_API_KEY_FILE")
        with open(self.api_key_file, "r") as f:
            self.api_key = f.read()

        # ------------------------------
        # Create sample customers
        # ------------------------------
        Partner = self.env["res.partner"]

        self.customer_1 = Partner.create({"name": "Customer A"})
        self.customer_2 = Partner.create({"name": "Customer B"})
        self.customer_3 = Partner.create({"name": "Customer C"})

        # ------------------------------
        # Create payments for last month
        # ------------------------------
        last_month_date = datetime.now() - timedelta(days=20)
        formatted = last_month_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        Payment = self.env["account.payment"]

        Payment.create({
            "partner_id": self.customer_1.id,
            "amount": 500,
            "payment_type": "inbound",
            "date": formatted,
        })

        Payment.create({
            "partner_id": self.customer_2.id,
            "amount": 200,
            "payment_type": "inbound",
            "date": formatted,
        })

        Payment.create({
            "partner_id": self.customer_1.id,
            "amount": 300,
            "payment_type": "inbound",
            "date": formatted,
        })

        Payment.create({
            "partner_id": self.customer_3.id,
            "amount": 900,
            "payment_type": "inbound",
            "date": formatted,
        })

        # ------------------------------
        # Initialize OpenAI client and test env override
        # ------------------------------
        self.client = OpenAIClient(api_key=self.api_key)
        self.override_env(self.env)
        self.override_openai_client(self.client)
        
    def test_query_return_a_plot(self):
        query = "Plot a bar chart of the top payments in the last 30 days"
        plot_binary = tools.query_returning_plot(query)
        logger.info(plot_binary)
