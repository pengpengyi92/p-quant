"""Calibrate a public synthetic test fixture. Never interpret this as PWOL performance."""
import argparse
from dataclasses import asdict
from hashlib import sha256
import json
import math
from pathlib import Path
from random import Random

from pbacktest.engine import run_backtest
from pevluation.metrics import drawdowns, evaluate, returns_statistics

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "project/pwol-synthetic-demo/fixture.json"


def path_inputs(spec):
    rng = Random(spec["seed"])
    return [(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(spec["sessions"])]


def targets_for(spec):
    return {i: {"SYN_A": spec["weight_a_even"] if k % 2 == 0 else spec["weight_a_odd"],
                "SYN_B": 1 - (spec["weight_a_even"] if k % 2 == 0 else spec["weight_a_odd"])}
            for k, i in enumerate(range(0, spec["sessions"], spec["rebalance_every_sessions"]))}


def make_returns(shocks, drift, scale, spread):
    return [{"SYN_A": math.expm1(drift + scale*z + spread*cross),
             "SYN_B": math.expm1(drift + scale*z - spread*cross)} for z,cross in shocks]


def run_fixture(spec):
    if (spec["scope"] != "CALIBRATED_SYNTHETIC_DEMO_ONLY" or spec["market_data"] is not False
            or spec["risk_free_annual"] != 0):
        raise ValueError("not a public synthetic demo fixture")
    shocks = path_inputs(spec)
    targets = targets_for(spec)
    n = len(shocks)
    initial, bps, spread = (spec[k] for k in ("initial_nav", "cost_bps", "spread_noise"))
    target_nav = initial * (1 + spec["target_return"])
    desired = spec["target_sharpe"]

    def route(drift, scale):
        return run_backtest(make_returns(shocks, drift, scale, spread), targets,
                            initial_nav=initial, cost_bps=bps)

    def at(scale):
        # Both sleeves are fully invested after the first trade. A constant
        # common log shift rescales wealth by exp(drift * n); homogeneous bps
        # fees do not break that scaling.
        a = route(0, scale).sessions[-1].nav
        drift = math.log(target_nav / a) / n
        run = route(drift, scale)
        ss = returns_statistics((s.net_return for s in run.sessions),
                                periods=spec["periods_per_year"])["sharpe"]
        return ss, drift, run

    lo, hi = spec["scale_bracket"]
    if not at(lo)[0] > desired > at(hi)[0]:
        raise ValueError("target outside the published calibration bracket")
    for _ in range(49):
        mid = (lo + hi) / 2
        if at(mid)[0] > desired:
            lo = mid
        else:
            hi = mid
    scale = (lo + hi) / 2
    _, drift, run = at(scale)
    m = evaluate(run, periods=spec["periods_per_year"], risk_free_annual=0)
    if abs(m["total_return"] - spec["target_return"]) > 1e-8 or abs(m["sharpe"] - desired) > 1e-8:
        raise ArithmeticError("calibration did not reproduce both targets")
    return run, m, {"fitted_common_log_drift_per_session":drift, "fitted_shock_multiplier":scale,
                    "spread_noise":spread, "uses_entire_synthetic_path":True,
                    "out_of_sample":"NOT_APPLICABLE",
                    "drawdown_is_observed_not_fitted":True}


def stable_json(obj):
    return (json.dumps(obj, ensure_ascii=False, allow_nan=False, indent=2)+"\n").encode("utf-8")


def execute(fixture, output):
    raw = fixture.read_bytes()
    spec = json.loads(raw)
    run, metrics, calibration = run_fixture(spec)
    summary = {
        "schema_version":1, "title":"PWOL-style portfolio calibrated synthetic demonstration",
        "author":spec["author"], "timestamp":spec["timestamp"], "scope":spec["scope"],
        "attribution":"Not actual PWOL holdings, returns, or investment evidence",
        "market_data":False, "execution_authorized":False,
        "fixture_sha256":sha256(raw).hexdigest(),
        "calibration":calibration,
        "drawdown_target_abs_max":spec["illustrative_drawdown_ceiling"],
        "drawdown_within_illustrative_ceiling":abs(metrics["max_drawdown"]) <= spec["illustrative_drawdown_ceiling"],
        "rebalance_every_sessions":spec["rebalance_every_sessions"], "cost_bps":spec["cost_bps"],
        "metrics":metrics,
    }
    fields = ["session","nav","daily_net_return","drawdown","gross_turnover","fees"]
    dd = drawdowns([r.nav for r in run.sessions],run.initial_nav)
    rows = [[0,run.initial_nav,0,0,0,0]]
    rows.extend([s.index,s.nav,s.net_return,d,s.gross_turnover,s.fees] for s,d in zip(run.sessions,dd))
    output.mkdir(parents=True, exist_ok=False)
    (output/"summary.json").write_bytes(stable_json(summary))
    body = json.dumps({"scope":spec["scope"], "columns":fields},ensure_ascii=False)
    # One record per line for review, without repeating field names.
    block = body[:-1] + ', "rows": [\n' + ',\n'.join(
        '  '+json.dumps(row,allow_nan=False,separators=(",",":")) for row in rows
    ) + '\n]}\n'
    (output/"series.json").write_bytes(block.encode("utf-8"))
    (output/"fills.json").write_bytes(stable_json({"scope":spec["scope"],"rows":[asdict(f) for f in run.fills]}))
    print(json.dumps({k:metrics[k] for k in ("total_return","sharpe","max_drawdown",
                                            "gross_turnover_excluding_open","total_fees")},indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture",type=Path,default=FIXTURE)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    execute(a.fixture,a.output)
