from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.addons.chartly.core.openai import OpenAIClient, create_function_tool
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
from odoo.addons.chartly.core import tools
import os

from logging import getLogger
logger = getLogger(__name__)

@tagged('integration', 'billed')
class TestExecuteQuery(TransactionCase):

    def override_openai_client(self, client):
        tools._openai_client_override = client

    def override_env(self, env):
        tools._env = env

    def setUp(self):
        super().setUp()
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

        # ------------------------------
        # Override OpenAI client and env in tools
        # ------------------------------
        self.override_env(self.env)
        self.override_openai_client(self.client)

        # ------------------------------
        # Prepare tools
        # ----------------------------
        plot_tool = create_function_tool(
            name="query_returning_plot",
            description="Generates a plot image based on the provided natural language query.",
            parameters= {
                "query": {
                    "type": "string",
                    "description": "The natural language query describing the plot to generate."
                }
            }, 
            required=["query"]
        )
        retrieve_tool = create_function_tool(
            name="query_returning_text",
            description="Executes a natural language query and returns the results as text.",
            parameters= {
                "query": {
                    "type": "string",
                    "description": "The natural language query to execute against the database."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return."
                }
            }, 
            required=["query"]
        )
        self.tools_descriptions = [plot_tool, retrieve_tool]
        self.tools = {
            "query_returning_text": {
                "return_type": "text",
                "tool_callable": tools.query_returning_text,
            },
            "query_returning_plot": {
                "return_type": "image",
                "tool_callable": tools.query_returning_plot,
            }
        }

    def _get_system_message(self):
        return"""You are an intelligent Odoo assistant specialized in invoicing and accounting.
Your purpose is to help the user interact with the Odoo database, specifically restricted
to invoice and account-related models. You have access to two tools:
* Data Retrieval Tool - takes a query and returns a list of textual results.
* Data Plotting Tool - takes a query and return a an iamge name.

Rules & Behavior:
Confirm ambiguous queries before executing.
Keep textual responses concise and structured.

Style:
Use a professional and helpful tone."""

    def test_call_plot_tool(self):
        query = "Plot a bar chart of the top 3 customers by payments and their total payments in the last 30 days"
        messages = []
        messages = self.client.add_system_message(messages, self._get_system_message())
        messages = self.client.add_user_message(messages, query)
        result = self.client.chat_completion_with_tools(messages, self.tools_descriptions, self.tools)
        if not result['success']:
            logger.info(f"Error executing request: {result['error']}")
        self.assertTrue(result['success'])
        self.assertTrue("image" in result)
        logger.info(f"Plot tool response content: {result['content']} \n Cost: {result.get('cost')}")

    def test_call_retrieve_tool(self):
        query = "Give the top 3 customers by payments and their total payments in the last 30 days"
        messages = []
        messages = self.client.add_system_message(messages, self._get_system_message())
        messages = self.client.add_user_message(messages, query)
        result = self.client.chat_completion_with_tools(messages, self.tools_descriptions, self.tools)
        if not result['success']:
            logger.info(f"Error executing request: {result['error']}")
        self.assertTrue(result['success'])
        logger.info(f"Retrieve tool response content: {result['content']} \n Cost: {result.get('cost')}")