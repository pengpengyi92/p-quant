"""Additive net contribution from the marked, per-asset backtest ledger."""
from math import fsum,isclose


def partition_contributions(run, taxonomy, start=1, end=None):
    """Net P&L / opening capital at window start, not standalone sector return."""
    end = len(run.sessions) if end is None else end
    if run.asset_marks is None or not (1<=start<=end<=len(run.sessions)):
        raise ValueError("missing marks or invalid attribution interval")
    initial = run.initial_nav if start==1 else run.sessions[start-2].nav
    marked = run.asset_marks[start-1:end]
    if not taxonomy or any(set(row)!=set(taxonomy) for row in marked):
        raise ValueError("taxonomy must cover every modeled asset, without ambiguity")
    sectors, industries = {},{}
    for asset,t in sorted(taxonomy.items()):
        sector,industry=t["sector"],t["industry"]
        for group,key in ((sectors,sector),(industries,sector+" / "+industry)):
            p=group.setdefault(key,{"gross_pnl":0.,"fees":0.})
            p["gross_pnl"]+=fsum(row[asset].gross_pnl for row in marked)
            p["fees"]+=fsum(row[asset].fee for row in marked)
    for grouping in (sectors,industries):
        for p in grouping.values():
            p["net_pnl"]=p["gross_pnl"]-p["fees"]
            p["net_contribution_pp"]=100*p["net_pnl"]/initial
    actual = run.sessions[end-1].nav-initial
    errors = [fsum(p["net_pnl"] for p in g.values())-actual for g in (sectors,industries)]
    if not all(isclose(e,0,abs_tol=initial*1e-11) for e in errors):
        raise ArithmeticError("asset contributions do not reconcile to equity")
    return {"opening_nav":initial,"net_pnl":actual,"compound_window_return":actual/initial,
            "sector":sectors,"industry":industries,"max_abs_reconciliation_residual":max(map(abs,errors))}


def guard_effects(metrics, attribution):
    """Positive drawdown reduction and positive foregone rebound (both in pp)."""
    p,q=metrics["original"],metrics["guarded"]
    reb={k:v["rebound"]["compound_window_return"] for k,v in attribution.items()}
    return {"drawdown_reduction_pp":100*(abs(p["max_drawdown"])-abs(q["max_drawdown"])),
            "terminal_net_return_change_pp":100*(q["total_return"]-p["total_return"]),
            "rebound_returns":reb,"rebound_foregone_pp":100*(reb["original"]-reb["guarded"])}
