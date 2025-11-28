from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.addons.chartly.core.openai import OpenAIClient
from odoo.addons.chartly.core.query_to_plot import query_to_plot
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
import os

from logging import getLogger
logger = getLogger(__name__)

@tagged('unit', 'billed', 'query_to_plot')
class TestOpenAIClientLive(TransactionCase):

    def setUp(self):
        super().setUp()

        # ------------------------------
        # Load API key
        # ------------------------------
        self.api_key_file = os.environ.get("OPENAI_API_KEY_FILE")
        with open(self.api_key_file, "r") as f:
            self.api_key = f.read()
        self.model = os.environ.get("OPENAI_MODEL")
        self.client = OpenAIClient(self.api_key, self.model)

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

    def test_query_to_plot(self):

        query = "Plot a bar chart of the top 10 customers by payments in the last month"

        model = "account.payment"
        domain = [
            ("payment_type", "=", "inbound"),
        ]

        Payment = self.env[model]

        records = Payment.search(domain)

        attributes = records[0]._fields.keys()

        self.client = OpenAIClient(api_key=self.api_key)

        plot_script = query_to_plot(self.client, query, attributes)

        logger.info(f"Plot Script: \n {plot_script}")

        self.assertTrue(plot_script)
