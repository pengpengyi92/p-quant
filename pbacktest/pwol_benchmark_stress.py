"""One replayed calibrated fixture plus a truly unfitted synthetic downside scenario."""
import argparse
from hashlib import sha256
import json
from math import expm1, isclose
from pathlib import Path
from random import Random

from pbacktest.engine import run_backtest
from pbacktest.pwol_demo import FIXTURE, ROOT, path_inputs, run_fixture, stable_json, targets_for
from pevluation.metrics import evaluate
from pevluation.relative import compare_matched_returns

PROTOCOL = ROOT / "project/pwol-benchmark-stress/protocol.json"


def base_index(base, cfg):
    if cfg["fee_bps"] != 0:
        raise ValueError("index is modeled fee-free")
    noise = Random(cfg["seed"])
    return [expm1(cfg["fixed_log_drift"] + cfg["shared_factor_loading"]*z +
                  cfg["independent_noise"]*noise.gauss(0,1)) for z,_ in path_inputs(base)]


def stress_input(n, cfg):
    if (cfg["parameters_fitted_to_performance"] is not False or
            cfg["benchmark_fee_bps"] != 0 or
            any(key in cfg for key in ("target_return","target_sharpe","target_drawdown"))):
        raise ValueError("stress inputs must be unfitted")
    shock_by_day = {}
    for w in cfg["shock_windows"]:
        a,b = w["first"],w["last"]
        if not 1<=a<=b<=n or w["log_shock"]>=0:
            raise ValueError("bad stress window")
        for i in range(a,b+1):
            if i in shock_by_day:
                raise ValueError("overlapping stress windows")
            shock_by_day[i] = w["log_shock"]

    g = Random(cfg["seed"])
    p, bench = [], []
    for i in range(1,n+1):
        common = cfg["common_noise"]*g.gauss(0,1) + shock_by_day.get(i,0.)
        spread = cfg["asset_spread_noise"]*g.gauss(0,1)
        index_noise = cfg["benchmark_independent_noise"]*g.gauss(0,1)
        port_log = cfg["portfolio_fixed_log_drift"] + cfg["portfolio_loading"]*common
        p.append({"SYN_A":expm1(port_log+spread),"SYN_B":expm1(port_log-spread)})
        bench.append(expm1(cfg["benchmark_fixed_log_drift"]+common+index_noise))
    return p,bench


def evaluate_case(run, index, spec):
    p = {s.index:s.net_return for s in run.sessions}
    b = dict(enumerate(index,1))
    m, ts = compare_matched_returns(p,b,periods=spec["periods_per_year"],risk_free_annual=spec["risk_free_annual"])
    if not isclose(ts["rows"][-1][1],run.sessions[-1].nav/run.initial_nav,rel_tol=1e-12):
        raise ArithmeticError("relative analysis did not reconcile with the ledger")
    return m, ts


def execute(protocol, output):
    spec = json.loads(protocol.read_bytes())
    data = FIXTURE.read_bytes()
    h = sha256(data).hexdigest()
    if (spec["scope"] != "SYNTHETIC_ONLY_NO_TRADE" or spec["market_data"] is not False
            or spec["execution_authorized"] is not False or spec["original_fixture_sha256"] != h):
        raise ValueError("synthetic-only protocol or original input hash mismatch")
    base = json.loads(data)
    horizon = spec["horizon"]
    if any(horizon[k]!=base[k] for k in horizon):
        raise ValueError("unmatched analysis horizon")
    rr, _, _=run_fixture(base)
    calibr, first = evaluate_case(rr,base_index(base,spec["base_benchmark"]),horizon)
    px,bx=stress_input(base["sessions"],spec["stress"])
    ss=run_backtest(px,targets_for(base),initial_nav=base["initial_nav"],cost_bps=base["cost_bps"])
    stress,second=evaluate_case(ss,bx,horizon)
    case = {"calibrated":{"metrics":calibr,"ledger":evaluate(rr),"portfolio_calibrated":True,
                          "benchmark_calibrated":False,"benchmark_id":spec["base_benchmark"]["id"],
                          "stress_windows":[]},
            "unfitted_stress":{"metrics":stress,"ledger":evaluate(ss),"portfolio_calibrated":False,
                               "benchmark_calibrated":False,"benchmark_id":spec["stress"]["id"],
                               "stress_windows":spec["stress"]["shock_windows"]}}
    summary = {"title":spec["title"],"author":spec["author"],"timestamp":spec["freeze_at"],"scope":spec["scope"],
               "market_data":False,"execution_authorized":False,"protocol_sha256":sha256(protocol.read_bytes()).hexdigest(),
               "original_fixture_sha256":h,
               "warning":"Generated benchmarks and paths, not actual PWOL holdings or performance.",
               "stress_input_sha256":sha256(stable_json([px,bx])).hexdigest(),
               "cases":case}
    output.mkdir(parents=True,exist_ok=False)
    (output/"summary.json").write_bytes(stable_json(summary))
    content='{"scope":'+json.dumps(spec["scope"])+', "columns":'+json.dumps(first["columns"])+', "cases": {'
    blocks=[]
    for k,v in (("calibrated",first),("unfitted_stress",second)):
        blocks.append(json.dumps(k)+': [\n'+',\n'.join('  '+json.dumps(r,separators=(",",":"),allow_nan=False)
                      for r in v["rows"])+'\n]')
    (output/"comparison-series.json").write_bytes((content+'\n'+',\n'.join(blocks)+'\n}}\n').encode("utf-8"))
    print(json.dumps({k:{kk:vv for kk,vv in v["metrics"].items()} for k,v in case.items()},indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol",type=Path,default=PROTOCOL)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    execute(a.protocol,a.output)
