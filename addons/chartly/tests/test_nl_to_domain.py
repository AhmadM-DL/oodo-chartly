import logging
from odoo.tests.common import TransactionCase
from odoo.addons.chartly.core.openai import OpenAIClient
from odoo.addons.chartly.core.utils import parse_odoo_domain, get_model_fields
from odoo.addons.chartly.core.nl_to_domain import nl_to_domain
import os, csv

# We tried alot of configuration tempretaure / model 
# Used LLM as a judge for 26 queries
# Change the prompt a lot - best was many shot like 10 examples - 84% accuracy
# Some failuers were valid though

from logging import getLogger
logger = getLogger(__name__)

class TestOpenAIClientLive(TransactionCase):

    def setUp(self):
        super().setUp()
        self.api_key_file = os.environ.get("OPENAI_API_KEY_FILE")
        with open(self.api_key_file, "r") as f:
            self.api_key = f.read()
        self.client = OpenAIClient(self.api_key)

    def test_nl_to_domain_csv(self):
        """Load CSV with NL → domain pairs and compare outputs."""
        csv_path = os.path.join(os.path.dirname(__file__), "nl_domain_test_pairs.csv")

        failures = 0
        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            total_rows = 0
            for row in reader:
                total_rows += 1
                query = row["Query"]
                expected_model = row["Model"]
                expected_domain = row["Domain"]

                fields = get_model_fields(expected_model)

                # logger.info(f"Testing query: {query} on model: {expected_model} with fields: {fields}")

                try:
                    result = nl_to_domain(self.client, query, expected_model, fields)
                except Exception as e:
                    failures+=1
                    logger.info(f"Query: {query} led to exception: {e}")
                    continue

                if result.get('not_safe', None):
                    logger.info(f"Query: {query} led to unsafe domain: \n {result['domain']}")
                    continue

                if result.get('not_formatted', None):
                    failures+=1
                    logger.info(f"Query: {query} led to not well formatted domain: \n {result['domain']}")
                    continue

                try:
                    domain_result = result.get("domain", "[]")
                    domain_result = parse_odoo_domain(domain_result)
                    domain_expected = parse_odoo_domain(expected_domain)
                    domain_match = set(domain_result) == set(domain_expected)
                except Exception as e:
                    failures+=1
                    logger.info(f"Query: {query} failed to eval domain: {e} \n {domain_result}")
                    continue

                if not domain_match:
                    failures+=1
                    logger.info(f"Query: {query} \n Expected: {domain_expected} \n Got: {domain_result}")
                
        self.fail(f"We have {failures}/{total_rows} fails.")