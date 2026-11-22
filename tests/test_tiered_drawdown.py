import json
import unittest

from pbacktest.engine import run_backtest
from pbacktest.pwol_tiered_drawdown import PROTOCOL, replay, scenario_panels
from pbacktest.tiered_policy import TieredDrawdownPolicy
from pevluation.attribution import partition_contributions
from pevluation.tier_review import review_tiers


class TieredDrawdownTests(unittest.TestCase):
    def setUp(self):
        self.spec=json.loads(PROTOCOL.read_bytes())

    def policy(self):
        return TieredDrawdownPolicy(100.,**self.spec["tiered"])

    def test_skip_down_but_restore_one_tier_with_clock_and_confirmation(self):
        p=self.policy()
        for t,v in enumerate([100,80,93,88,95,95,95,95,95,95,95]):
            p(t,v,{"a":1.} if t==0 else None)
        self.assertEqual([(q.decision_session,q.fill_session,q.target_exposure)
                          for q in p.trace if q.action!="hold"],
                         [(1,2,.25),(4,5,.5),(7,8,.75)])
        self.assertEqual(p.trace[-1].target_exposure,.75) # 5% is not within the 4% exit

    def test_failed_confirmation_resets_and_deeper_cut_ignores_cooldown(self):
        p=self.policy()
        for t,v in enumerate([100,93,89,94,91,95,95,97,97,97]):
            p(t,v,{"a":1.} if t==0 else None)
        self.assertEqual([(q.decision_session,q.target_exposure) for q in p.trace if q.action!="hold"],
                         [(1,.75),(2,.5),(6,.75),(9,1.)])

    def test_gap_applied_before_fill_and_not_seen_until_next_decision(self):
        p=self.policy()
        run=run_backtest([{"a":0.}]*3,{0:{"a":1.}},initial_nav=100.,cost_bps=0.,
                         overnight=[{"a":0.},{"a":-.20},{"a":.125}],
                         target_policy=p,track_attribution=True)
        self.assertEqual([r.nav for r in run.sessions],[100.,80.,90.])
        self.assertEqual([(q.action,q.target_exposure) for q in p.trace],
                         [("hold",1.),("hold",1.),("reduce",.25)])
        self.assertEqual([(f.decision_session,f.fill_session,f.signed_notional) for f in run.fills],
                         [(0,1,100.),(2,3,-67.5)]) # 90 -> 22.50, after that open's gap
        self.assertEqual(run.sessions[2].gross_turnover,.75)
        self.assertAlmostEqual(run.sessions[2].net_return,.125)
        self.assertEqual([q["a"].overnight_pnl for q in run.asset_marks],[0.,-20.,10.])
        tax={"a":{"sector":"One","industry":"I"}}
        self.assertAlmostEqual(partition_contributions(run,tax)["net_pnl"],-10.)

    def test_order_targets_invariant_to_current_and_future_prices(self):
        def run(shock, later):
            p=self.policy()
            ledger=run_backtest([{"a":-.12},{"a":shock},{"a":later}],{0:{"a":1.}},initial_nav=100.,
                                overnight=[{"a":0.},{"a":shock},{"a":later}],target_policy=p)
            return p,ledger
        a,x=run(.10,.30)
        b,y=run(-.10,-.30)
        self.assertEqual(a.trace[:2],b.trace[:2])
        self.assertEqual(x.fills[0],y.fills[0])
        self.assertEqual(a.trace[1].target_exposure,.5)
        self.assertNotEqual(x.fills[1].signed_notional,y.fills[1].signed_notional) # same target, different open price

    def test_no_gap_panel_matches_legacy_and_gap_panel_must_align(self):
        inside=[{"a":.03},{"a":-.1}]; schedule={0:{"a":.75}}
        run=lambda **kw: run_backtest(inside,schedule,track_attribution=True,**kw)
        self.assertEqual(run(),run(overnight=[{"a":0.}]*2))
        with self.assertRaises(ValueError):
            run(overnight=[{"a":0.}])
        with self.assertRaises(ValueError):
            run(overnight=[{"a":0.},{"a":-1.}])

    def test_fixed_costs_common_benchmark_attribution_and_gate(self):
        spec=self.spec
        for case in spec["cases"].values():
            opening,day=scenario_panels(252,spec["assets"],spec["shocks"],case)
            bench=run_backtest(day,{0:{k:.25 for k in spec["assets"]}},cost_bps=0.,
                               overnight=opening,track_attribution=True)
            low,_,attribute=replay(spec,case,opening,day,5,bench)
            high,_,_=replay(spec,case,opening,day,15,bench)
            self.assertEqual(low["metrics"]["benchmark"],high["metrics"]["benchmark"])
            for k,windows in attribute.items():
                for w in windows.values():
                    self.assertLess(w["max_abs_reconciliation_residual"],1e-6)
                    self.assertAlmostEqual(sum(v["net_contribution_pp"] for v in w["industry"].values()),
                                           100*w["compound_window_return"])
        synthetic=lambda d:{"max_drawdown":d,"total_return":0.,"gross_turnover_excluding_open":0.,
                            "fees_pct_initial_nav":0.}
        values={k:synthetic(v) for k,v in zip(("original","binary","tiered"),(-.2,-.1,-.125))}
        gate=review_tiers(values,{"binary":.1,"tiered":.2},.8)
        self.assertTrue(gate["passes_rebound_gate"])
        self.assertFalse(gate["passes_joint_gate"])


if __name__=="__main__":
    unittest.main()
