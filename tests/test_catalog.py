import copy
from pathlib import Path
import unittest

from scripts.validate_catalog import ROOT, load, run_reference, validate, validate_entries


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.entries = load(ROOT/"repo/catalog.json")["entries"]
        self.fixture = load(ROOT/"project/synthetic-backtest-comparison/protocol.json")

    def test_catalog_and_link_consistency(self):
        status = validate()
        self.assertEqual(status["categories"],5)
        self.assertEqual(status["sections"],7)
        self.assertGreater(status["entries"],20)
        self.assertEqual(status["external_benchmarks"],"UNMEASURED")

    def test_duplicate_id_or_upstream_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"duplicate id"):
            validate_entries(self.entries+[copy.deepcopy(self.entries[0])])
        row = dict(self.entries[0], id="second-id")
        with self.assertRaisesRegex(ValueError,"duplicate upstream"):
            validate_entries(self.entries+[row])

    def test_wrong_transport_and_unearned_claims_are_rejected(self):
        with self.assertRaisesRegex(ValueError,"noncanonical"):
            validate_entries([dict(self.entries[0],upstream="http://github.com/test/repo")])
        with self.assertRaisesRegex(ValueError,"upstream-reviewed"):
            validate_entries([dict(self.entries[0],benchmark="FASTEST")])

    def test_baseline_cost_and_fill_clock(self):
        o = run_reference(self.fixture)
        self.assertEqual(o["equity"],[1000,1009,1018])
        self.assertEqual(o["quantity"],[0,10,0])
        self.assertEqual(run_reference(self.fixture,2)["cash"][-1],1016)

    def test_missing_open_rejected_without_lookahead(self):
        x = copy.deepcopy(self.fixture)
        x["bar"][1]["open"] = None
        with self.assertRaisesRegex(ValueError,"next-open"):
            run_reference(x)
        y = copy.deepcopy(self.fixture)
        y["bar"][1]["open"] = 80
        self.assertEqual(run_reference(y)["cash"][0],1000)
