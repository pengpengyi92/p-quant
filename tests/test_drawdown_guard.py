import json
from math import fsum
import unittest

from pbacktest.drawdown_policy import DrawdownPolicy
from pbacktest.engine import run_backtest
from pbacktest.pwol_drawdown_guard import PROTOCOL,run_case
from pevluation.attribution import partition_contributions

CFG={"reduce_on_drawdown":.08,"restore_within_drawdown":.04,
     "reduced_target":.50,"minimum_completed_sessions":5}


class DrawdownGuardTests(unittest.TestCase):
    def test_hysteresis_requires_five_completed_reduced_sessions(self):
        s=DrawdownPolicy(100,**CFG)
        self.assertEqual(s(0,100,{"A":1}),{"A":1})
        self.assertEqual(s(1,91,None),{"A":.5})
        for j in range(2,6):
            self.assertIsNone(s(j,98,None))
        self.assertEqual(s(6,98,None),{"A":1})
        self.assertEqual([(z["action"],z["fill_session"]) for z in s.switches()],
                         [("reduce",2),("restore",7)])

    def test_future_session_does_not_change_that_open_trade(self):
        x=DrawdownPolicy(100,**CFG)
        y=DrawdownPolicy(100,**CFG)
        a=run_backtest([{"A":-.10},{"A":.8}],{0:{"A":1}},initial_nav=100,target_policy=x)
        b=run_backtest([{"A":-.10},{"A":-.3}],{0:{"A":1}},initial_nav=100,target_policy=y)
        self.assertEqual(a.fills,b.fills)
        self.assertEqual(x.trace,y.trace)
        self.assertEqual(a.fills[-1].decision_session,1)
        self.assertEqual(a.fills[-1].fill_session,2)
        self.assertNotEqual(a.sessions[-1].nav,b.sessions[-1].nav)

    def test_unfilled_target_and_invalid_risk_weights(self):
        with self.assertRaises(ValueError):
            run_backtest([{"A":.1}],{0:{"A":1}},target_policy=lambda t,nav,w:{"A":1.5})
        with self.assertRaises(ValueError):
            DrawdownPolicy(100,**{**CFG,"restore_within_drawdown":.12})

    def test_sector_industry_reconcile_with_costs_and_cash(self):
        tax={"A":{"sector":"X","industry":"One"},"B":{"sector":"X","industry":"Two"}}
        r=run_backtest([{"A":.01,"B":.02},{"A":-.10,"B":.03}],{0:{"A":.5,"B":.4},1:{"B":.5}},
                       initial_nav=100,cost_bps=5,track_attribution=True)
        for start in (1,2):
            a=partition_contributions(r,tax,start,2)
            for k in ("sector","industry"):
                self.assertAlmostEqual(fsum(x["net_contribution_pp"] for x in a[k].values()),
                                       100*a["compound_window_return"])
        self.assertGreater(a["sector"]["X"]["fees"],0)

    def test_three_distinct_unfitted_paths_and_common_benchmark(self):
        p=json.loads(PROTOCOL.read_bytes())
        self.assertEqual(len({c["seed"] for c in p["cases"].values()}),3)
        self.assertTrue(p["calibration"].startswith("NONE;"))
        for label,cfg in p["cases"].items():
            with self.subTest(case=label):
                x,z,a=run_case(p,cfg)
                self.assertLess(x["metrics"]["original"]["max_drawdown"],0)
                bm=x["metrics"]["benchmark"]["total_return"]
                self.assertEqual(x["vs_same_benchmark"]["original"]["benchmark_total_return"],bm)
                self.assertEqual(x["vs_same_benchmark"]["guarded"]["benchmark_total_return"],bm)
                self.assertEqual(len(z),253)
                self.assertTrue(all(s["fill_session"]==s["decision_session"]+1 for s in x["switches"]))
                self.assertLess(a["guarded"]["full"]["max_abs_reconciliation_residual"],1e-5)
