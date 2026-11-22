"""Compute portfolio statistics from a net NAV and fill ledger."""
from math import fsum, isfinite, prod, sqrt
from statistics import fmean, stdev


def drawdowns(nav, initial_nav):
    """Signed daily drawdown relative to the high-water mark, including initial NAV."""
    peak = initial_nav
    out = []
    for v in nav:
        peak = max(peak, v)
        out.append(v / peak - 1)
    return out


def returns_statistics(net_returns, *, periods=252, risk_free_annual=0.0):
    r = tuple(net_returns)
    if (not r or type(periods) is not int or periods <= 0 or
            any(not isfinite(x) or x <= -1 for x in r) or
            not isfinite(risk_free_annual) or risk_free_annual <= -1):
        raise ValueError("invalid return series or annualization")
    rf_daily = (1 + risk_free_annual) ** (1 / periods) - 1
    excess = [x - rf_daily for x in r]
    sigma = stdev(excess) if len(r) >= 2 else 0
    downside = sqrt(fmean(min(0, x) ** 2 for x in excess))
    gain, loss = fsum(max(0, x) for x in r), fsum(max(0, -x) for x in r)
    total = prod(1 + x for x in r)
    return {
        "total_return": total - 1,
        "cagr": total ** (periods / len(r)) - 1,
        "annual_volatility": sigma * sqrt(periods) if len(r) >= 2 else None,
        "sharpe": sqrt(periods) * fmean(excess) / sigma if sigma else None,
        "sortino": sqrt(periods) * fmean(excess) / downside if downside else None,
        "win_rate": sum(x > 0 for x in r) / len(r),
        "daily_profit_factor": gain / loss if loss else None,
        "best_session_return": max(r),
        "worst_session_return": min(r),
    }


def evaluate(run, *, periods=252, risk_free_annual=0.0):
    rows = run.sessions
    m = returns_statistics([s.net_return for s in rows], periods=periods,
                           risk_free_annual=risk_free_annual)
    d = drawdowns([s.nav for s in rows], run.initial_nav)
    max_drawdown = min(0.0, *d)
    duration, longest = 0, 0
    for value in d:
        duration = (duration + 1) if value < -1e-12 else 0
        longest = max(longest, duration)
    costs = fsum(f.fee for f in run.fills)
    opening_deploy = rows[0].gross_turnover
    ongoing_turnover = fsum(row.gross_turnover for row in rows[1:])
    return {
        **m,
        "max_drawdown": max_drawdown,
        "longest_underwater_sessions": longest,
        "calmar": m["cagr"] / abs(max_drawdown) if max_drawdown < 0 else None,
        "initial_nav": run.initial_nav,
        "ending_nav": rows[-1].nav,
        "gross_turnover_including_open": opening_deploy + ongoing_turnover,
        "gross_turnover_excluding_open": ongoing_turnover,
        "half_gross_turnover_excluding_open": ongoing_turnover / 2,
        "initial_deployment_turnover": opening_deploy,
        "total_fees": costs,
        "fees_pct_initial_nav": costs / run.initial_nav,
        "sessions": len(rows),
        "rebalance_sessions_including_open": sum(row.gross_turnover > 0 for row in rows),
        "fills": len(run.fills),
        "periods_per_year": periods,
        "risk_free_annual": risk_free_annual,
    }
