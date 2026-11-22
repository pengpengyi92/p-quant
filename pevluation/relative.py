"""Matched portfolio and benchmark metrics; risk-free and annualization explicit."""
from math import fsum, isfinite, prod, sqrt
from statistics import fmean, stdev

from pevluation.metrics import drawdowns, returns_statistics

EPSILON = 1e-14


def compare_matched_returns(portfolio, benchmark, *, periods=252, risk_free_annual=0.0):
    """Accept two schedules keyed by the same consecutive session IDs."""
    if not portfolio or set(portfolio) != set(benchmark) or any(type(k) is not int for k in portfolio):
        raise ValueError("return observations must have the same integer session IDs")
    t = sorted(portfolio)
    if any(b != a + 1 for a,b in zip(t,t[1:])):
        raise ValueError("session IDs must be consecutive")
    p, b = [portfolio[i] for i in t], [benchmark[i] for i in t]
    pm = returns_statistics(p, periods=periods,risk_free_annual=risk_free_annual)
    bm = returns_statistics(b, periods=periods,risk_free_annual=risk_free_annual)
    rf = (1 + risk_free_annual) ** (1/periods) - 1
    active = [x-y for x,y in zip(p,b)]
    track = stdev(active) if len(active)>1 else None
    x, y = [j-rf for j in b], [j-rf for j in p]
    mx, my = fmean(x),fmean(y)
    denominator = fsum((j-mx)**2 for j in x)
    beta = (fsum((i-mx)*(j-my) for i,j in zip(x,y))/denominator
            if denominator > len(x)*EPSILON**2 and len(x)>1 else None)
    alpha = my - beta*mx if beta is not None else None

    weights_p = [1.0]
    weights_b = [1.0]
    for ap,ab in zip(p,b):
        weights_p.append(weights_p[-1]*(1+ap))
        weights_b.append(weights_b[-1]*(1+ab))
    relative_nav = [a / d for a,d in zip(weights_p,weights_b)]
    if any(not isfinite(i) or i<=0 for i in weights_p+weights_b+relative_nav):
        raise ValueError("invalid compounded wealth path")
    dp = drawdowns(weights_p,1.)
    db = drawdowns(weights_b,1.)
    dr = drawdowns(relative_nav,1.)

    metrics = {
        "portfolio_total_return":pm["total_return"], "benchmark_total_return":bm["total_return"],
        "cumulative_excess_pct_points":100*(pm["total_return"]-bm["total_return"]),
        "relative_compounded_return":relative_nav[-1]-1,
        "annualized_mean_active_return":periods*fmean(active),
        "annualized_tracking_error":track*sqrt(periods) if track is not None else None,
        "information_ratio":sqrt(periods)*fmean(active)/track if track is not None and track>EPSILON else None,
        "ols_alpha_daily":alpha,
        "ols_alpha_annual_arithmetic":alpha*periods if alpha is not None else None,
        "ols_beta":beta,
        "portfolio_max_drawdown":min(dp), "benchmark_max_drawdown":min(db),
        "relative_max_drawdown":min(dr),
        "portfolio_sharpe":pm["sharpe"], "benchmark_sharpe":bm["sharpe"],
        "observations":len(t),"periods_per_year":periods,"risk_free_annual":risk_free_annual
    }
    return metrics, {
        "columns":["session","portfolio_nav","benchmark_nav","relative_nav",
                   "portfolio_drawdown","benchmark_drawdown","relative_drawdown"],
        "rows":[list(v) for v in zip([t[0]-1,*t],weights_p,weights_b,relative_nav,dp,db,dr)]
    }
