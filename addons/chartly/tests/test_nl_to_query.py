from odoo.tests.common import TransactionCase
from odoo.addons.chartly.core.openai import OpenAIClient
from odoo.addons.chartly.core.utils import parse_odoo_domain
from odoo.addons.chartly.core.nl_to_query import nl_to_query
import os, csv

# We tried alot of configuration tempretaure / model 
# Used LLM as a judge for 50 queries
# Change the prompt a lot - best was many shot like 40 examples - 70% success
# Some failuers were valid others were not
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

                if result.get('not_restricted', None):
                    failures.append(f"Query: {query} led to unrestricted domain:\n {result['domain']}")
                    continue

                if result.get('not_safe', None):
                    failures.append(f"Query: {query} led to unsafe domain: \n {result['domain']}")
                    continue

                if result.get('not_formatted', None):
                    failures.append(f"Query: {query} led to not well formatted domain: \n {result['domain']}")
                    continue

                # Compare model
                model_match = (expected_model == "ERROR" and result.get("error")) or (result.get("model") == expected_model)
                
                # Compare domain if no error
                if expected_model != "ERROR":
                    try:
                        domain_result = result.get("domain", "[]")
                        domain_result = parse_odoo_domain(domain_result)
                        domain_expected = parse_odoo_domain(expected_domain)
                        domain_match = set(domain_result) == set(domain_expected)
                    except Exception as e:
                        failures.append(f"Query: {query} failed to eval domain: {e} \n {domain_result}")
                        continue
                else:
                    domain_match = "error" in result

                if not (model_match and domain_match):
                    failures.append(
                        f"Query: {query}\nExpected: model={expected_model}, domain={expected_domain}\nGot: {result['model']}, {result['domain']}"
                    )

        if failures:
            failures_str = "\n\n".join(failures)
            self.fail(f"We have {len(failures)}/50 fails. \n {failures_str}")
