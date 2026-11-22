import copy
import json
from math import sqrt
from pathlib import Path
from statistics import fmean, stdev
from tempfile import TemporaryDirectory
import unittest

from pbacktest.pwol_benchmark_stress import PROTOCOL, ROOT, execute, stress_input
from pevluation.relative import compare_matched_returns


class BenchmarkStressTests(unittest.TestCase):
    def test_ols_and_ir_known_roles(self):
        x=[-.03,.02,.01,-.005]
        y=[.001+.8*v for v in x]
        a=[p-q for p,q in zip(y,x)]
        m,_=compare_matched_returns(dict(enumerate(y)),dict(enumerate(x)))
        self.assertAlmostEqual(m["ols_beta"],.8)
        self.assertAlmostEqual(m["ols_alpha_annual_arithmetic"],.252)
        self.assertAlmostEqual(m["information_ratio"],sqrt(252)*fmean(a)/stdev(a))

    def test_undefined_ratios_stay_undefined(self):
        paths={1:.02,2:-.01,3:.00}
        m,_=compare_matched_returns(paths,paths)
        self.assertIsNone(m["information_ratio"])
        self.assertAlmostEqual(m["ols_beta"],1.)
        self.assertAlmostEqual(m["ols_alpha_daily"],0)
        m,_=compare_matched_returns(paths,{1:0,2:0,3:0})
        self.assertIsNone(m["ols_beta"])
        self.assertIsNone(m["ols_alpha_daily"])

    def test_reject_mismatch_or_gaps(self):
        with self.assertRaisesRegex(ValueError,"same"):
            compare_matched_returns({1:.01,2:.02},{2:.01,3:.02})
        with self.assertRaisesRegex(ValueError,"consecutive"):
            compare_matched_returns({1:0,3:0},{1:0,3:0})

    def test_compound_excess_and_drawdown(self):
        m,out=compare_matched_returns({1:-.20,2:.30},{1:-.10,2:.10})
        self.assertAlmostEqual(m["cumulative_excess_pct_points"],5.)
        self.assertAlmostEqual(m["relative_compounded_return"],1.04/.99-1)
        self.assertAlmostEqual(m["portfolio_max_drawdown"],-.20)
        self.assertAlmostEqual(m["benchmark_max_drawdown"],-.10)
        self.assertEqual(out["rows"][0],[0,1.,1.,1.,0.,0.,0.])

    def test_unfitted_generator_rejects_targets(self):
        s=json.loads(PROTOCOL.read_bytes())["stress"]
        x,y=stress_input(252,s)
        self.assertEqual((x,y),stress_input(252,copy.deepcopy(s)))
        with self.assertRaisesRegex(ValueError,"unfitted"):
            stress_input(252,{**s,"target_return":-.2})

    def test_original_nav_unchanged_and_stress_is_down(self):
        with TemporaryDirectory() as tmp:
            out=Path(tmp)/"run"
            import contextlib
            import io
            with contextlib.redirect_stdout(io.StringIO()):
                execute(PROTOCOL,out)
            base=json.loads((ROOT/"project/pwol-synthetic-demo/artifacts/series.json").read_bytes())["rows"]
            r=json.loads((out/"comparison-series.json").read_bytes())["cases"]["calibrated"]
            self.assertEqual(len(base),len(r))
            for a,b in zip(base,r):
                self.assertEqual(a[0],b[0])
                self.assertAlmostEqual(a[1]/base[0][1],b[1],places=12)
            summary=json.loads((out/"summary.json").read_bytes())
            stress=summary["cases"]["unfitted_stress"]
            self.assertFalse(stress["portfolio_calibrated"] or stress["benchmark_calibrated"])
            self.assertLess(stress["metrics"]["portfolio_total_return"],0)
            self.assertLess(stress["metrics"]["benchmark_total_return"],0)
