"""A fractional, long-only synthetic portfolio ledger. No venue or data clients."""
from dataclasses import asdict, dataclass
from math import fsum, isfinite

ZERO = 1e-12


@dataclass(frozen=True)
class Session:
    index: int
    nav: float
    cash: float
    net_return: float
    fees: float
    buys: float
    sells: float
    gross_turnover: float


@dataclass(frozen=True)
class Fill:
    decision_session: int
    fill_session: int
    asset: str
    signed_notional: float
    fee: float


@dataclass
class Run:
    initial_nav: float
    sessions: list[Session]
    fills: list[Fill]

    def session_rows(self) -> list[dict]:
        return [asdict(row) for row in self.sessions]


def _target_value(nav, positions, weights, fee_rate):
    """Solve value + fee rate times gross turnover = value before trade."""
    if fee_rate == 0:
        return nav
    left, right = 0.0, nav
    for _ in range(52):
        mid = (left + right) / 2
        fees = fee_rate * fsum(abs(mid * weights[a] - positions[a]) for a in positions)
        if mid + fees > nav:
            right = mid
        else:
            left = mid
    return (left + right) / 2


def run_backtest(returns, targets, *, initial_nav=1_000_000.0, cost_bps=5.0):
    """Execute targets issued at t-1 before applying return for session t.

    Index 0 is the starting mark; returns[0] is session 1 close-to-close.
    The toy open is the previous close (no gaps). The engine doesn't use a
    session's realized returns when calculating its opening trades.
    """
    if not returns or not returns[0] or not isfinite(initial_nav) or initial_nav <= 0:
        raise ValueError("need positive initial NAV and a nonempty return panel")
    if not isfinite(cost_bps) or not 0 <= cost_bps < 1000:
        raise ValueError("cost_bps must be in [0, 1000)")
    assets = sorted(returns[0])
    names = set(assets)
    n = len(returns)
    for t, w in targets.items():
        if (type(t) is not int or not 0 <= t < n or not set(w) <= names
                or any(not isfinite(v) or v < 0 for v in w.values())
                or fsum(w.values()) > 1 + ZERO):
            raise ValueError("invalid target date, instrument or long-only weight")
    fee_rate = cost_bps / 10_000
    cash, nav = float(initial_nav), float(initial_nav)
    pos = dict.fromkeys(assets, 0.0)
    rows, fills = [], []
    for t, day in enumerate(returns, 1):
        if set(day) != names or any(not isfinite(x) or x <= -1 for x in day.values()):
            raise ValueError("invalid or missing asset return")
        nav_at_open = nav
        buys = sells = fees = 0.0
        target = targets.get(t - 1)
        if target is not None:
            w = {a: target.get(a, 0.0) for a in assets}
            weights_sum = fsum(w.values())
            if weights_sum > 1:  # only a floating-point remainder is permitted
                w = {a: x / weights_sum for a,x in w.items()}
                weights_sum = 1.
            free_nav = _target_value(nav, pos, w, fee_rate)
            next_pos = {a: free_nav * w[a] for a in assets}
            for a in assets:
                delta = next_pos[a] - pos[a]
                if delta:
                    fill_fee = abs(delta) * fee_rate
                    fills.append(Fill(t - 1, t, a, delta, fill_fee))
                    buys += max(delta, 0)
                    sells += max(-delta, 0)
                    fees += fill_fee
            cash -= buys - sells + fees
            if not abs(cash - free_nav * (1 - weights_sum)) < 1e-9 * nav_at_open:
                raise ArithmeticError("cash must fund trades and fees")
            cash = max(cash, 0.0)
            pos = next_pos
        pos = {a: pos[a] * (1 + day[a]) for a in assets}
        nav = cash + fsum(pos.values())
        if not isfinite(nav) or nav <= 0:
            raise ArithmeticError("insolvency or nonfinite equity")
        rows.append(Session(t, nav, cash, nav / nav_at_open - 1, fees, buys, sells,
                            (buys + sells) / nav_at_open))
    return Run(float(initial_nav), rows, fills)
