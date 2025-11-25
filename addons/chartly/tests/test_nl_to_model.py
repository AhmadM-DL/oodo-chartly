from odoo.tests.common import TransactionCase
from odoo.addons.chartly.core.nl_to_model import nl_to_model
from odoo.addons.chartly.core.openai import OpenAIClient
import csv, os
import logging

logger = logging.getLogger(__name__)

# Hard examples

# Query: Generate a chart of taxes collected per tax group
# Expected: ['account.tax.repartition.line', 'account.tax.group']
# Got: ['account.tax', 'account.tax.group']
# “Taxes collected” → LLM interprets it as general account.tax objects (the tax definitions) rather than how taxes are actually applied and summed per move line, which is account.tax.repartition.line.
# account.tax.repartition.line is more technical / implementation-specific, and the LLM doesn’t “know” that unless the prompt explicitly teaches it.

# Query: Generate a chart of taxes collected per tax group
# Expected: ['account.tax.repartition.line', 'account.tax.group']
# Got: ['account.tax', 'account.tax.group', 'account.tax.repartition.line']

class TestNLToModelCSV(TransactionCase):

    def setUp(self):
        super().setUp()
        self.api_key_file = os.environ.get("OPENAI_API_KEY_FILE")
        with open(self.api_key_file, "r") as f:
            self.api_key = f.read()
        self.model = os.environ.get("OPENAI_MODEL")
        self.client = OpenAIClient(self.api_key, self.model)

        self.csv_path = os.path.join(os.path.dirname(__file__), "nl_model_test_pairs.csv")

        self.test_cases = []
        with open(self.csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                query = row["Query"]
                models = [m.strip() for m in row["Models"].split(",")]
                self.test_cases.append((query, models))

    def test_nl_to_model_from_csv(self):

        failures = []
        for query, expected_models in self.test_cases:
            models_result = nl_to_model(client=self.client, text=query)
            logger.info("Query: %s -> Models: %s", query, models_result)
            if not set(expected_models) == (set(models_result)):
                failures.append(f"Query: {query}\nExpected: {expected_models}\nGot: {models_result}")

        logger.info("Finished test with %d/%d failures", len(failures), len(self.test_cases))
        if failures:
            self.fail("\n\n".join(failures))