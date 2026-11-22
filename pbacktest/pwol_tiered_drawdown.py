"""Replay frozen synthetic close-to-open and open-to-close returns."""
import argparse
from hashlib import sha256
import json
from math import expm1, fsum
from pathlib import Path
from random import Random

from pbacktest.drawdown_policy import DrawdownPolicy
from pbacktest.engine import run_backtest
from pbacktest.pwol_demo import ROOT, stable_json
from pbacktest.pwol_drawdown_guard import nav_rows, net_series, target_weights
from pbacktest.tiered_policy import TieredDrawdownPolicy
from pevluation.attribution import partition_contributions
from pevluation.metrics import evaluate
from pevluation.relative import compare_matched_returns
from pevluation.tier_review import review_tiers

PROTOCOL=ROOT/"project/pwol-tiered-drawdown/protocol.json"
KEYS=("original","binary","tiered","benchmark")


def scenario_panels(n, taxonomy, shocks, case):
    rng=Random(case["seed"])
    sectors=sorted({v["sector"] for v in taxonomy.values()})
    inside, outside={}, {}
    for lo,hi,shift in case["intraday_shifts"]:
        if not 1<=lo<=hi<=n or any(t in inside for t in range(lo,hi+1)):
            raise ValueError("overlapping or out-of-range shift")
        inside.update({t:shift for t in range(lo,hi+1)})
    for s,x in case["overnight_gaps"].items():
        if not 2<=int(s)<=n:
            raise ValueError("invalid gap session")
        outside[int(s)]=x
    opening, daytime=[],[]
    for t in range(1,n+1):
        m=shocks["base_log_drift"]+rng.gauss(0,shocks["market_sigma"])+inside.get(t,0.)
        local={s:rng.gauss(0,shocks["sector_sigma"]) for s in sectors}
        opening.append({a:expm1(v["loading"]*outside.get(t,0.))
                        for a,v in sorted(taxonomy.items())})
        daytime.append({a:expm1(v["loading"]*m+local[v["sector"]]+rng.gauss(0,shocks["industry_sigma"]))
                        for a,v in sorted(taxonomy.items())})
    return opening,daytime


def replay(spec, case, opening, daytime, cost_bps, benchmark):
    s, tax=spec["samples"],spec["assets"]
    initial=s["initial_nav"]
    weights=target_weights(len(daytime),tax,s)
    kw={"initial_nav":initial,"cost_bps":cost_bps,"overnight":opening,"track_attribution":True}
    variants={
        "original":run_backtest(daytime,weights,**kw),
        "benchmark":benchmark,
    }
    policies={"binary":DrawdownPolicy(initial,**spec["binary"]),
              "tiered":TieredDrawdownPolicy(initial,**spec["tiered"])}
    for k,policy in policies.items():
        variants[k]=run_backtest(daytime,weights,**kw,target_policy=policy)
    windows={"full":[1,len(daytime)],"rebound":case["rebound_window"]}
    if "relapse_window" in case:
        windows["relapse"]=case["relapse_window"]
    if case["overnight_gaps"]:
        g=int(next(iter(case["overnight_gaps"])))
        windows["gap_session"]=[g,g]
    attribution={k:{name:partition_contributions(variants[k],tax,*bounds)
                    for name,bounds in windows.items()} for k in KEYS}
    metrics={k:evaluate(variants[k]) for k in KEYS}
    rebound={k:v["rebound"]["compound_window_return"] for k,v in attribution.items()}
    common=net_series(benchmark)
    summary={
        "cost_bps":cost_bps,
        "metrics":metrics,
        "vs_same_benchmark":{k:compare_matched_returns(net_series(variants[k]),common)[0]
                             for k in KEYS if k!="benchmark"},
        "window_returns":{name:{k:v[name]["compound_window_return"] for k,v in attribution.items()}
                          for name in windows if name!="full"},
        "switches":{k:[{**event,
                         "actual_gross_turnover":variants[k].sessions[event["fill_session"]-1].gross_turnover,
                         "actual_fee":variants[k].sessions[event["fill_session"]-1].fees}
                        for event in p.switches()] for k,p in policies.items()},
        **review_tiers(metrics,rebound,spec["success"]["min_fraction_binary_drawdown_improvement"]),
    }
    if case["overnight_gaps"]:
        if len(case["overnight_gaps"])!=1:
            raise ValueError("gap analysis expects one isolated gap")
        summary["gap_detail"]={
            k:{
                "overnight_return_before_fills":fsum(a.overnight_pnl for a in v.asset_marks[g-1].values())
                                                /v.sessions[g-2].nav,
                "open_sells":v.sessions[g-1].sells,
                "same_day_net_return":v.sessions[g-1].net_return,
            } for k,v in variants.items()
        }
    paths={k:nav_rows(v) for k,v in variants.items()}
    targets=[[1.,*(p.target_exposure for p in policies[k].trace)] for k in ("binary","tiered")]
    rows=[list(r) for r in zip(range(len(daytime)+1),*(paths[k][0] for k in KEYS),
                              *(paths[k][1] for k in KEYS),*targets)]
    return summary,rows,attribution


def execute(protocol, output):
    raw=protocol.read_bytes()
    spec=json.loads(raw)
    if (spec["scope"]!="SYNTHETIC_ONLY_NO_TRADE" or spec["market_data"] is not False
            or spec["execution_authorized"] is not False or not spec["calibration"].startswith("NONE;")
            or set(spec["cases"])!={"new_v","gap","false"}
            or len({x["seed"] for x in spec["cases"].values()})!=3):
        raise ValueError("requires three frozen synthetic cases")
    s,tax=spec["samples"],spec["assets"]
    summary={"title":spec["title"],"author":spec["author"],"timestamp":spec["frozen_at"],
             "scope":spec["scope"],"protocol_sha256":sha256(raw).hexdigest(),
             "market_data":False,"execution_authorized":False,"cases":{}}
    series={"scope":spec["scope"],"plot_precision_decimals":8,
            "columns":["session",*(k+"_nav" for k in KEYS),*(k+"_drawdown" for k in KEYS),
                       "binary_exposure","tiered_exposure"],"cases":{}}
    attribution={"scope":spec["scope"],"taxonomy":tax,"cases":{}}
    for name, case in spec["cases"].items():
        opening,daytime=scenario_panels(s["sessions"],tax,spec["shocks"],case)
        benchmark=run_backtest(daytime,{0:{a:1/len(tax) for a in tax}},initial_nav=s["initial_nav"],
                               overnight=opening,cost_bps=0.,track_attribution=True)
        primary,rows,attr=replay(spec,case,opening,daytime,s["cost_bps"],benchmark)
        sensitivity,_,_=replay(spec,case,opening,daytime,s["sensitivity_bps"],benchmark)
        summary["cases"][name]={"design":case,"input_sha256":sha256(stable_json([opening,daytime])).hexdigest(),
                                "primary":primary,"sensitivity":sensitivity}
        series["cases"][name]=[[r[0],*(round(x,8) for x in r[1:])] for r in rows]
        attribution["cases"][name]=attr
    output.mkdir(parents=True,exist_ok=False)
    (output/"summary.json").write_bytes(stable_json(summary))
    (output/"series.json").write_bytes((json.dumps(series,separators=(",",":"),allow_nan=False)+"\n").encode("utf-8"))
    (output/"attribution.json").write_bytes(stable_json(attribution))
    print(json.dumps({k:{f:c["primary"][f] for f in ("tiered_drawdown_saved_pp","tiered_minus_binary_window_net_pp","passes_joint_gate")}
                      for k,c in summary["cases"].items()},indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol",type=Path,default=PROTOCOL)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    execute(a.protocol,a.output)
