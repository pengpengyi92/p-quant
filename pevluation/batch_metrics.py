"""Matched, fee-inclusive batch metrics and the frozen joint decision."""
from math import fsum, prod
from statistics import median

from pevluation.metrics import evaluate

VARIANTS = ("original", "binary", "tiered", "benchmark")


def path_metrics(run, windows):
    def value(t):
        return run.initial_nav if t==0 else run.sessions[t-1].nav
    ev = evaluate(run)
    legs = [100*(value(b)/value(a-1)-1) for name,(a,b) in windows.items() if name!="full"]
    return {
        "max_drawdown_pp": 100*ev["max_drawdown"],
        "full_return_pp": 100*ev["total_return"],
        "rebound_pp": 100*(prod(1+x/100 for x in legs)-1),
        "legs_pp": legs,
        "turnover_pp": 100*ev["gross_turnover_excluding_open"],
        "commission_bps": 10_000*fsum(f.fee for f in run.fills)/run.initial_nav,
        "slippage_bps": 10_000*fsum(f.slippage for f in run.fills)/run.initial_nav,
        "fillable_sessions": sum(row.gross_turnover>0 for row in run.sessions),
    }


def gate_result(policy_metrics, gate):
    o,b,t = (policy_metrics[k] for k in ("original","binary","tiered"))
    eps = gate["mdd_eps_pp"]
    protect_binary = b["max_drawdown_pp"]-o["max_drawdown_pp"]
    protect_tiered = t["max_drawdown_pp"]-o["max_drawdown_pp"]
    better_rebound = t["rebound_pp"]-b["rebound_pp"]
    full_delta = t["full_return_pp"]-b["full_return_pp"]
    dd = protect_tiered>eps and protect_tiered+eps>=max(protect_binary,0)*gate["min_binary_dd_fraction"]
    rebound = better_rebound>eps
    full = full_delta+eps>=-gate["max_full_period_shortfall_pp"]
    return {
        "dd_gate":dd, "rebound_gate":rebound, "full_gate":full,
        "short_joint":dd and rebound, "joint":dd and rebound and full,
        "binary_mdd_saved_pp":protect_binary, "tiered_mdd_saved_pp":protect_tiered,
        "tiered_minus_binary_rebound_pp":better_rebound, "tiered_minus_binary_full_pp":full_delta,
        "tiered_minus_binary_worst_leg_pp":min(x-y for x,y in zip(t["legs_pp"],b["legs_pp"])),
    }


def aggregate_cases(cases, profiles, gate):
    families = ("all", *dict.fromkeys(x["family"] for x in cases))
    agg={}
    def minimum(rows, value):
        row=min(rows,key=value)
        return {"path_id":row["path_id"],"value":value(row)}
    for p in profiles:
        agg[p]={}
        for f in families:
            cohort=[r for r in cases if f=="all" or r["family"]==f]
            pack=lambda r: r["profiles"][p]
            counts={flag:sum(pack(r)["gate"][flag] for r in cohort)
                    for flag in ("dd_gate","rebound_gate","full_gate","short_joint","joint")}
            stats={}
            for k in VARIANTS:
                entry=lambda r:pack(r)["variants"][k]
                stats[k]={
                    "worst_mdd":minimum(cohort,lambda r:entry(r)["max_drawdown_pp"]),
                    "worst_full":minimum(cohort,lambda r:entry(r)["full_return_pp"]),
                    **{"median_"+v:median(entry(r)[v] for r in cohort)
                       for v in ("max_drawdown_pp","full_return_pp","rebound_pp","turnover_pp",
                                 "commission_bps","slippage_bps")},
                    "median_total_cost_bps":median(entry(r)["commission_bps"]+entry(r)["slippage_bps"] for r in cohort),
                    "median_full_excess_vs_benchmark_pp":median(
                        entry(r)["full_return_pp"]-pack(r)["variants"]["benchmark"]["full_return_pp"] for r in cohort),
                }
            worst={k:minimum(cohort,lambda r:pack(r)["gate"][k])
                   for k in ("tiered_minus_binary_rebound_pp","tiered_minus_binary_full_pp",
                             "tiered_minus_binary_worst_leg_pp")}
            medians={k:median(pack(r)["gate"][k] for r in cohort) for k in worst}
            agg[p][f]={"n":len(cohort),"gate_counts":counts,"variants":stats,
                       "worst_paired":worst,"median_paired":medians}
    research_gate=all(
        agg[p]["all"]["variants"]["tiered"]["worst_mdd"]["value"]+gate["mdd_eps_pp"]
        >=agg[p]["all"]["variants"]["binary"]["worst_mdd"]["value"]
        and all(agg[p][f]["gate_counts"]["joint"]/agg[p][f]["n"]>=gate["min_joint_fraction_each_family"]
                for f in families if f!="all")
        for p in profiles)
    return agg,research_gate
