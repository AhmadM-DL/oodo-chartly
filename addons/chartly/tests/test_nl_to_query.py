# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.addons.chartly.core.utils import OpenAIClient
from odoo.addons.chartly.core.nl_to_query import nl_to_query
import os, csv, ast

class TestOpenAIClientLive(TransactionCase):

    def setUp(self):
        super().setUp()
        self.api_key_file = os.environ.get("OPENAI_API_KEY_FILE")
        with open(self.api_key_file, "r") as f:
            self.api_key = f.read()
        self.client = OpenAIClient(self.api_key)

    def test_nl_to_query_csv(self):
        """Load CSV with NL → domain pairs and compare outputs."""
        csv_path = os.path.join(os.path.dirname(__file__), "nl_query_pairs.csv")

        failures = []
        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                query = row["Query"]
                expected_model = row["Model"]
                expected_domain = row["Domain"]

                try:
                    result = nl_to_query(self.client, query)
                except Exception as e:
                    failures.append(f"Query: {query} raised exception {e}")
                    continue

                # Compare model
                model_match = (expected_model == "ERROR" and result.get("error")) or (result.get("model") == expected_model)
                
                # Compare domain if no error
                if expected_model != "ERROR":
                    try:
                        domain_result = ast.literal_eval(result.get("domain", "[]"))
                        domain_expected = ast.literal_eval(expected_domain)
                        domain_match = set(domain_result) == set(domain_expected)
                    except Exception as e:
                        failures.append(f"Query: {query} failed to eval domain: {e}")
                        continue
                else:
                    domain_match = "error" in result

                if not (model_match and domain_match):
                    failures.append(
                        f"Query: {query}\nExpected: model={expected_model}, domain={expected_domain}\nGot: {result}"
                    )

        if failures:
            print(f"We have {len(failures)}/50 fails.")
