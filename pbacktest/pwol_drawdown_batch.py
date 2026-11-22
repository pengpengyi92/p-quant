"""Frozen synthetic stress batch and a Python/SQLite ledger reconciliation."""
import argparse
from contextlib import closing
from hashlib import sha256
import json
from pathlib import Path
from random import Random
import sqlite3

from pbacktest.drawdown_policy import DrawdownPolicy
from pbacktest.engine import run_backtest
from pbacktest.pwol_demo import ROOT, stable_json
from pbacktest.pwol_drawdown_guard import target_weights
from pbacktest.pwol_tiered_drawdown import PROTOCOL as BASELINE, scenario_panels
from pbacktest.tiered_policy import TieredDrawdownPolicy
from pevluation.batch_metrics import VARIANTS, aggregate_cases, gate_result, path_metrics
from pevluation.sql_ledger import audit_ledger, create_ledger, expected_attribution, write_path, write_variant

PROJECT = ROOT/"project/pwol-drawdown-batch"
PROFILE_KEYS = ("primary","stress")
FAMILIES = ("fast_v","gap_chain","fake_cycles","combined")


def case_designs(spec):
    d = spec["seed_design"]
    seen=set()
    for family,offset in zip(FAMILIES,d["offsets"],strict=True):
        template=spec["families"][family]
        for i in range(d["count_per_family"]):
            seed=d["start"]+offset+i
            if seed in seen:
                raise ValueError("duplicated seed")
            seen.add(seed)
            rand=Random(seed^d["structure_rng_xor"])
            scale=rand.uniform(d["magnitude_min"],d["magnitude_max"])
            shift=rand.randint(-d["clock_shift_max"],d["clock_shift_max"])
            windows={"full":(1,spec["sessions"])}
            for j,(a,b) in enumerate(template["rebound_legs"],1):
                windows[f"leg_{j}"]=a+shift,b+shift
            end=0
            for a,b in list(windows.values())[1:]:
                if not end<a<=b<=spec["sessions"]:
                    raise ValueError("overlapping or invalid rebound legs")
                end=b
            yield (
                {"path_id":f"{family}-{seed}","family":family,"seed":seed,"shock_scale":scale,"clock_shift":shift},
                {"seed":seed,
                 "intraday_shifts":[(a+shift,b+shift,m*scale) for a,b,m in template["intraday_shifts"]],
                 "overnight_gaps":{str(int(t)+shift):v*scale for t,v in template["overnight_gaps"].items()}},
                windows,
            )


def trial(daytime, opening, baseline, initial, profile, benchmark):
    weights=target_weights(len(daytime),baseline["assets"],baseline["samples"])
    cost={k:v for k,v in profile.items() if k!="commission_bps"}
    kw={"initial_nav":initial,"overnight":opening,"track_attribution":True,
        "cost_bps":profile["commission_bps"],**cost}
    binary=DrawdownPolicy(initial,**baseline["binary"])
    tiered=TieredDrawdownPolicy(initial,**baseline["tiered"])
    runs={
        "original":run_backtest(daytime,weights,**kw),
        "binary":run_backtest(daytime,weights,**kw,target_policy=binary),
        "tiered":run_backtest(daytime,weights,**kw,target_policy=tiered),
        "benchmark":benchmark,
    }
    return runs,{"binary":binary.trace,"tiered":tiered.trace}


def load_frozen(protocol):
    raw=protocol.read_bytes()
    spec=json.loads(raw)
    old=BASELINE.read_bytes()
    if (spec["scope"]!="SYNTHETIC_ONLY_NO_TRADE" or spec["market_data"] is not False
            or spec["execution_authorized"] is not False or spec["baseline_sha256"]!=sha256(old).hexdigest()
            or set(spec["profiles"])!=set(PROFILE_KEYS) or set(spec["families"])!=set(FAMILIES)
            or not spec["calibration"].startswith("NONE;")):
        raise ValueError("invalid synthetic batch or baseline hash")
    return spec,json.loads(old),sha256(raw).hexdigest()


def representative(meta, design, windows, runs, decisions):
    return {
        "path_id":meta["path_id"],"family":meta["family"],"design":design,"windows":windows,
        "nav":{k:[1.,*(round(s.nav/r.initial_nav,8) for s in r.sessions)] for k,r in runs.items()},
        "exposure":{k:[1.,*(x.target_exposure for x in trace)] for k,trace in decisions.items()},
    }


def run_into(db, spec, baseline, schema):
    tax=baseline["assets"]
    create_ledger(db,schema,tax)
    cases, expectations, attribution = [], {}, {}
    demo = None
    initial,n=spec["initial_nav"],spec["sessions"]
    for meta,design,windows in case_designs(spec):
        opening,daytime=scenario_panels(n,tax,baseline["shocks"],design)
        meta["input_sha256"]=sha256(stable_json([opening,daytime])).hexdigest()
        write_path(db,meta,windows)
        bench=run_backtest(daytime,{0:{a:1/len(tax) for a in tax}},initial_nav=initial,cost_bps=0,
                           overnight=opening,track_attribution=True)
        by_profile={}
        for p in PROFILE_KEYS:
            runs,decisions=trial(daytime,opening,baseline,initial,spec["profiles"][p],bench)
            metrics={}
            for k in VARIANTS:
                run=runs[k]
                key=(meta["path_id"],p,k)
                m=path_metrics(run,windows)
                returns=dict(zip(windows,[m["full_return_pp"],*m["legs_pp"]],strict=True))
                expectations[key]=m,returns
                metrics[k]=m
                write_variant(db,key,run)
                attribution.update({(*key,*x):nums for x,nums in expected_attribution(run,tax,windows).items()})
            gate=gate_result(metrics,spec["gate"])
            by_profile[p]={"variants":metrics,"gate":gate}
            if p=="primary" and meta["family"]=="combined" and demo is None:
                demo=representative(meta,design,windows,runs,decisions)
        cases.append({**meta,"windows":windows,"profiles":by_profile})
    db.commit()
    sql_summary,attr_rows=audit_ledger(db,expectations,attribution,{c["path_id"]:c["family"] for c in cases})
    if db.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise ArithmeticError("orphan ledger row")
    return cases,sql_summary,attr_rows,demo


def execute(protocol, output, keep_db=False):
    spec,baseline,digest=load_frozen(protocol)
    schema=(PROJECT/"ledger.sql").read_text(encoding="utf-8")
    output.mkdir(parents=True,exist_ok=False)
    target=output/"ledger.sqlite" if keep_db else ":memory:"
    with closing(sqlite3.connect(target)) as db:
        cases,audit,attr,demo=run_into(db,spec,baseline,schema)
    groups,promote=aggregate_cases(cases,PROFILE_KEYS,spec["gate"])
    scope=spec["scope"]
    summary={k:spec[k] for k in ("title","author","frozen_at","scope","market_data","execution_authorized",
                                "gate","profiles")}
    summary.update({"protocol_sha256":digest,"baseline_sha256":spec["baseline_sha256"],
                    "families":{k:v["label"] for k,v in spec["families"].items()},"cohorts":groups,
                    "research_promotion_gate":promote,"sqlite_audit":audit})
    columns=["family","profile","variant","window","level","bucket","paths",
             "mean_gross_pp","mean_commission_pp","mean_slippage_pp","mean_net_pp"]
    (output/"summary.json").write_bytes(stable_json(summary))
    # One path per line keeps the table reviewable in version control.
    encoded=[json.dumps(x,separators=(",",":"),ensure_ascii=False,allow_nan=False) for x in cases]
    (output/"paths.json").write_bytes(("{\"scope\":"+json.dumps(scope)+",\"paths\":[\n"
                                      +",\n".join(encoded)+"\n]}\n").encode("utf-8"))
    (output/"attribution.json").write_bytes(stable_json({"scope":scope,"columns":columns,"rows":attr}))
    (output/"example.json").write_bytes(stable_json({"scope":scope,**demo}))
    print(json.dumps({"protocol_sha256":digest,"paths":len(cases),"promotion_gate":promote,
                      "primary":groups["primary"]["all"]["gate_counts"],"stress":groups["stress"]["all"]["gate_counts"],
                      "sqlite_audit":audit},indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol",type=Path,default=PROJECT/"protocol.json")
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--keep-db",action="store_true",help="write the full synthetic SQLite ledger as well")
    a=p.parse_args()
    execute(a.protocol,a.output,a.keep_db)
