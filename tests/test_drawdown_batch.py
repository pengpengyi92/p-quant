import sqlite3
import unittest

from pbacktest.engine import run_backtest
from pbacktest.pwol_drawdown_batch import PROJECT, case_designs, load_frozen
from pbacktest.pwol_tiered_drawdown import scenario_panels
from pevluation.batch_metrics import gate_result, path_metrics
from pevluation.sql_ledger import audit_ledger, create_ledger, expected_attribution, write_path, write_variant


class DrawdownBatchTests(unittest.TestCase):
    def setUp(self):
        self.spec,self.baseline,_=load_frozen(PROJECT/"protocol.json")

    def test_seed_universe_and_path_design_are_fixed(self):
        cases=list(case_designs(self.spec))
        self.assertEqual(cases,list(case_designs(self.spec)))
        self.assertEqual(len(cases),64)
        seeds={m["seed"] for m,_,_ in cases}
        self.assertEqual(len(seeds),64)
        self.assertFalse(seeds & {q["seed"] for q in self.baseline["cases"].values()})
        for m,c,w in cases:
            gaps=sorted(map(int,c["overnight_gaps"]))
            if m["family"]=="gap_chain":
                self.assertTrue(len(gaps)==3 and gaps[-1]-gaps[0]==2)
            self.assertEqual(len(w)-1,3 if m["family"] in ("fake_cycles","combined") else 1)
        m,c,_=cases[16]
        opening,day=scenario_panels(252,self.baseline["assets"],self.baseline["shocks"],c)
        self.assertEqual(sum(any(g.values()) for g in opening),3)
        self.assertEqual((opening,day),scenario_panels(252,self.baseline["assets"],self.baseline["shocks"],c))

    def test_slippage_cap_is_cash_charged_on_sell_after_marking_gap(self):
        run=run_backtest([{"a":0.}]*3,{0:{"a":1.},1:{}},initial_nav=100.,cost_bps=5,
                         overnight=[{"a":0.},{"a":-.2},{"a":0.}],track_attribution=True,
                         base_slippage_bps=6,gap_bps_per_pct=2,gap_cap_bps=35)
        buy,sell=run.fills
        self.assertAlmostEqual(buy.signed_notional,100/(1+.0011))
        self.assertAlmostEqual(buy.slippage/buy.signed_notional,.0006)
        self.assertAlmostEqual(sell.signed_notional,-buy.signed_notional*.8)
        self.assertAlmostEqual(sell.slippage/(-sell.signed_notional),.0041)
        self.assertAlmostEqual(run.asset_marks[1]["a"].overnight_pnl,-.2*buy.signed_notional)
        self.assertAlmostEqual(run.sessions[1].nav,-sell.signed_notional-sell.fee-sell.slippage)
        self.assertEqual(len(run.fills),2)
        self.assertAlmostEqual(run.sessions[-1].nav,run.sessions[-2].nav)

    def test_signal_targets_not_changed_by_future_open_or_late_intraday(self):
        def simulate(gap,intraday):
            seen=[]
            def policy(t,nav,schedule):
                seen.append((t,nav))
                return {"a":1.} if t==0 else {}
            result=run_backtest([{"a":0.},{"a":intraday}],{},target_policy=policy,
                                overnight=[{"a":0.},{"a":gap}],base_slippage_bps=6,
                                gap_bps_per_pct=2,gap_cap_bps=35)
            return seen,result.fills[-1]
        a,x=simulate(-.10,.8)
        b,y=simulate(.20,-.3)
        self.assertEqual(a,b)
        self.assertNotEqual(x.signed_notional,y.signed_notional)
        self.assertNotEqual(x.slippage,y.slippage)

    def test_joint_can_fail_on_full_period_even_after_short_pass(self):
        values={k:{"max_drawdown_pp":m,"rebound_pp":r,"legs_pp":[r],"full_return_pp":f}
                for k,m,r,f in (("original",-20,9,4),("binary",-15,5,2),("tiered",-16,6,1))}
        result=gate_result(values,self.spec["gate"])
        self.assertTrue(result["short_joint"])
        self.assertFalse(result["joint"])

    def test_sql_independently_reconciles_a_toy_ledger_and_rejects_bad_clock(self):
        run=run_backtest([{"a":.03},{"a":-.01},{"a":.04}],{0:{"a":1.},1:{"a":.5}},
                         initial_nav=1_234.0,overnight=[{"a":0.},{"a":-.15},{"a":.03}],
                         track_attribution=True,base_slippage_bps=6,gap_bps_per_pct=2,gap_cap_bps=35)
        tax={"a":{"sector":"S","industry":"I"}}
        meta={"path_id":"toy","family":"f","seed":1,"input_sha256":"test","shock_scale":1.,"clock_shift":0}
        windows={"full":(1,3),"leg_1":(3,3)}
        m=path_metrics(run,windows)
        key=("toy","primary","original")
        with sqlite3.connect(":memory:") as db:
            create_ledger(db,(PROJECT/"ledger.sql").read_text(encoding="utf-8"),tax)
            write_path(db,meta,windows)
            write_variant(db,key,run)
            actual,_=audit_ledger(db,{key:(m,dict(zip(windows,[m["full_return_pp"],*m["legs_pp"]])))},
                                  {(*key,*k):xs for k,xs in expected_attribution(run,tax,windows).items()},
                                  {"toy":"f"})
            self.assertEqual(actual["buckets_checked"],4)
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("UPDATE fills SET decision_session=fill_session")


if __name__=="__main__":
    unittest.main()
