import json
import unittest

from pbacktest.engine import run_backtest
from pbacktest.pwol_demo import FIXTURE, run_fixture
from pevluation.metrics import drawdowns, evaluate, returns_statistics


class PortfolioDemoTests(unittest.TestCase):
    def test_fill_timing_cash_notional_and_costs(self):
        x=run_backtest([{"A":.10},{"A":.11}],{0:{"A":1},1:{}},initial_nav=100,cost_bps=50)
        self.assertAlmostEqual(x.initial_nav,100)
        first=100/1.005
        self.assertAlmostEqual(x.sessions[0].nav,first*1.10)
        self.assertAlmostEqual(x.sessions[1].nav,first*1.10*.995)
        for f in x.fills:
            self.assertEqual(f.fill_session,f.decision_session+1)
            self.assertAlmostEqual(f.fee,abs(f.signed_notional)*.005)
        self.assertAlmostEqual(evaluate(x)["total_fees"],sum(r.fees for r in x.sessions))

    def test_trade_has_no_same_day_return_lookahead(self):
        a=run_backtest([{"X":.1}],{0:{"X":.8}})
        b=run_backtest([{"X":-.25}],{0:{"X":.8}})
        self.assertEqual(a.fills,b.fills)
        self.assertNotEqual(a.sessions[0].nav,b.sessions[0].nav)

    def test_reject_leverage_or_missing_assets(self):
        with self.assertRaises(ValueError):
            run_backtest([{"X":.1}],{0:{"X":1.2}})
        with self.assertRaises(ValueError):
            run_backtest([{"X":.1},{"Y":.1}],{0:{"X":1}})

    def test_max_drawdown_includes_opening_wealth(self):
        self.assertEqual(drawdowns([75,120,96,121],100)[0],-.25)
        self.assertAlmostEqual(drawdowns([75,120,96,121],100)[2],-.2)
        profile=returns_statistics([0,0])
        self.assertEqual(profile["total_return"],0)
        self.assertIsNone(profile["sharpe"])
        self.assertIsNone(profile["sortino"])

    def test_frozen_synthetic_demo_and_rebalance_cadence(self):
        spec=json.loads(FIXTURE.read_text(encoding="utf-8"))
        result,m,cal=run_fixture(spec)
        self.assertEqual(spec["scope"],"CALIBRATED_SYNTHETIC_DEMO_ONLY")
        self.assertAlmostEqual(m["total_return"],.5,places=8)
        self.assertAlmostEqual(m["sharpe"],5.,places=8)
        self.assertAlmostEqual(result.sessions[-1].nav,1500000,places=5)
        self.assertTrue(cal["drawdown_is_observed_not_fitted"])
        self.assertLessEqual(abs(m["max_drawdown"]),spec["illustrative_drawdown_ceiling"])
        self.assertEqual([s.index for s in result.sessions if s.gross_turnover>0],list(range(1,253,21)))
