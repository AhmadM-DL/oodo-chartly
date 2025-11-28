from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.addons.chartly.core.openai import OpenAIClient
from odoo.addons.chartly.core.utils import get_model_fields
from odoo.addons.chartly.core.nl_to_sql import nl_to_sql
import os, csv

from logging import getLogger
logger = getLogger(__name__)

@tagged('unit', "billed", 'nl_to_sql')
class TestOpenAIClientLive(TransactionCase):

    def setUp(self):
        super().setUp()
        self.api_key_file = os.environ.get("OPENAI_API_KEY_FILE")
        with open(self.api_key_file, "r") as f:
            self.api_key = f.read()
        self.model = os.environ.get("OPENAI_MODEL")
        self.client = OpenAIClient(self.api_key, self.model)

        self.csv_path = os.path.join(os.path.dirname(__file__), "nl_sql_test_pairs.csv")

        self.test_cases = []
        with open(self.csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                query = row["Query"]
                models = [m.strip() for m in row["Models"].split(",")]
                sql = row["SQL"]
                self.test_cases.append((query, models, sql))

    def test_nl_to_sql(self):
        failures = []
        for query, expected_models, sql in self.test_cases:
            fields = { model:get_model_fields(model) for model in expected_models}
            models_result = nl_to_sql(client=self.client, query=query, models=expected_models, fields=fields)
            generate_sql = models_result.get('sql_query')
            logger.info("Query: %s -> Models: %s", query, expected_models)
            if not set(sql) == (set(generate_sql)):
                failures.append(f"Query: {query}\nExpected: \n{sql}\nGot: \n{generate_sql}")
        logger.info("Finished test with %d/%d failures", len(failures), len(self.test_cases))
        if failures:
            self.fail("\n\n".join(failures))

    