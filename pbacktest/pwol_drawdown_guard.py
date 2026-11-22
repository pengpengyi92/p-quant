"""Matched synthetic stress replays with and without a drawdown reduction policy."""
import argparse
from hashlib import sha256
import json
from math import expm1
from pathlib import Path
from random import Random

from pbacktest.drawdown_policy import DrawdownPolicy
from pbacktest.engine import run_backtest
from pbacktest.pwol_demo import ROOT, stable_json
from pevluation.attribution import guard_effects, partition_contributions
from pevluation.metrics import drawdowns, evaluate
from pevluation.relative import compare_matched_returns

PROTOCOL=ROOT/"project/pwol-drawdown-guard/protocol.json"


def scenario_returns(n, tax, shocks, case):
    a,b=case["selloff"]
    c,d=case["rebound_window"]
    if not 1<=a<=b<c<=d<=n or case["selloff_log_shift"]>=0:
        raise ValueError("incorrect stress or recovery window")
    g=Random(case["seed"])
    sectors=sorted({x["sector"] for x in tax.values()})
    series=[]
    for t in range(1,n+1):
        x=shocks["base_log_drift"]+shocks["market_sigma"]*g.gauss(0,1)
        x+=(case["selloff_log_shift"] if a<=t<=b else
            case["rebound_log_shift"] if c<=t<=d else 0)
        noise={s:shocks["sector_sigma"]*g.gauss(0,1) for s in sectors}
        series.append({k:expm1(v["loading"]*x+noise[v["sector"]]+shocks["industry_sigma"]*g.gauss(0,1))
                       for k,v in sorted(tax.items())})
    return series


def target_weights(n,tax,s):
    # Preserve the prior demo's alternating two sleeve weights; split each equally by industry.
    counts={g:sum(v["sector"]==g for v in tax.values()) for g in ("Technology","Industrials")}
    if any(not i for i in counts.values()) or any(v["sector"] not in counts for v in tax.values()):
        raise ValueError("baseline needs the two declared synthetic sleeves")
    result={}
    for k,t in enumerate(range(0,n,s["rebalance_every"])):
        a=s["sector_a_even"] if k%2==0 else s["sector_a_odd"]
        alloc={"Technology":a,"Industrials":1-a}
        result[t]={x:alloc[v["sector"]]/counts[v["sector"]] for x,v in tax.items()}
    return result


def nav_rows(run):
    nav=[s.nav/run.initial_nav for s in run.sessions]
    return [1.,*nav],[0.,*drawdowns(nav,1.)]


def net_series(run):
    return {s.index:s.net_return for s in run.sessions}


def run_case(spec, case):
    s=spec["samples"]
    tax=spec["assets"]
    px=scenario_returns(s["sessions"],tax,spec["shocks"],case)
    weights=target_weights(len(px),tax,s)
    # Remove only human-readable metadata before building the policy.
    rules={k:v for k,v in spec["guard"].items() if k!="basis"}
    policy=DrawdownPolicy(s["initial_nav"],**rules)
    kw={"initial_nav":s["initial_nav"],"cost_bps":s["cost_bps"],"track_attribution":True}
    original=run_backtest(px,weights,**kw)
    guarded=run_backtest(px,weights,**kw,target_policy=policy)
    bench=run_backtest(px,{0:{a:1/len(tax) for a in tax}},**{**kw,"cost_bps":0.})
    b=net_series(bench)
    start,end=case["rebound_window"]
    variants={"original":original,"guarded":guarded,"benchmark":bench}
    metrics={k:evaluate(v) for k,v in variants.items()}
    relative={k:compare_matched_returns(net_series(v),b)[0] for k,v in variants.items() if k!="benchmark"}
    attr={k:{"full":partition_contributions(v,tax),"rebound":partition_contributions(v,tax,start,end)}
          for k,v in variants.items()}
    summary={"label":case["label"],"selloff":case["selloff"],"rebound_window":[start,end],
             "input_sha256":sha256(stable_json(px)).hexdigest(),
             "metrics":metrics,"vs_same_benchmark":relative,
             **guard_effects(metrics,attr),
             "switches":policy.switches(),"reduced_sessions":sum(x.target_exposure<1 for x in policy.trace)}
    nn,nd=nav_rows(original);gn,gd=nav_rows(guarded);bn,bd=nav_rows(bench)
    rows=[list(x) for x in zip(range(len(px)+1),nn,gn,bn,nd,gd,bd,
                              [1.,*(p.target_exposure for p in policy.trace)])]
    return summary,rows,attr


def execute(protocol, output):
    raw=protocol.read_bytes()
    spec=json.loads(raw)
    if (spec["scope"]!="SYNTHETIC_ONLY_NO_TRADE" or spec["market_data"] is not False
            or spec["execution_authorized"] is not False or not spec["calibration"].startswith("NONE;")
            or len(spec["cases"])!=3 or len({x["seed"] for x in spec["cases"].values()})!=3):
        raise ValueError("invalid frozen synthetic protocol")
    vals={key:run_case(spec,c) for key,c in spec["cases"].items()}
    result={"title":spec["title"],"author":spec["author"],"timestamp":spec["frozen_at"],"scope":spec["scope"],
            "market_data":False,"execution_authorized":False,"performance_calibration":False,
            "protocol_sha256":sha256(raw).hexdigest(),"cases":{k:v[0] for k,v in vals.items()}}
    columns=["session","original_nav","guarded_nav","benchmark_nav","original_drawdown",
             "guarded_drawdown","benchmark_drawdown","guarded_target_exposure"]
    series={"scope":spec["scope"],"columns":columns}
    head=json.dumps(series,ensure_ascii=False)
    body=',\n'.join(json.dumps(k)+': [\n'+',\n'.join("  "+json.dumps(z,separators=(",",":"),allow_nan=False) for z in v[1])+'\n]'
                     for k,v in vals.items())
    output.mkdir(parents=True,exist_ok=False)
    (output/"summary.json").write_bytes(stable_json(result))
    (output/"series.json").write_bytes((head[:-1]+', "cases": {\n'+body+'\n}}\n').encode("utf-8"))
    (output/"attribution.json").write_bytes(stable_json({"scope":spec["scope"],"taxonomy":spec["assets"],
                                                        "cases":{k:v[2] for k,v in vals.items()}}))
    print(json.dumps({k:{x:v[0][x] for x in ("drawdown_reduction_pp","rebound_foregone_pp","terminal_net_return_change_pp","reduced_sessions")}
                      for k,v in vals.items()},indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol",type=Path,default=PROTOCOL)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    execute(a.protocol,a.output)
