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


@dataclass(frozen=True)
class AssetMark:
    gross_pnl: float
    fee: float
    overnight_pnl: float = 0.


@dataclass
class Run:
    initial_nav: float
    sessions: list[Session]
    fills: list[Fill]
    asset_marks: list[dict[str, AssetMark]] | None = None

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


def _valid_target(w, names):
    return (set(w) <= names and all(isfinite(v) and v >= 0 for v in w.values())
            and fsum(w.values()) <= 1 + ZERO)


def run_backtest(returns, targets, *, initial_nav=1_000_000.0, cost_bps=5.0,
                 target_policy=None, track_attribution=False, overnight=None):
    """Execute targets issued at t-1 before applying return for session t.

    Index 0 is the starting mark. With no overnight panel, the toy open equals
    the last close. Otherwise pre-existing holdings take the close-to-open
    return first; returns supplies open-to-close returns. A target submitted
    on yesterday's close is sized at the realized open, not at the stale close.
    A policy receives only the decision ID, prior close NAV and scheduled target.
    """
    if not returns or not returns[0] or not isfinite(initial_nav) or initial_nav <= 0:
        raise ValueError("need positive initial NAV and a nonempty return panel")
    if not isfinite(cost_bps) or not 0 <= cost_bps < 1000:
        raise ValueError("cost_bps must be in [0, 1000)")
    assets = sorted(returns[0])
    names = set(assets)
    n = len(returns)
    if overnight is not None and len(overnight) != n:
        raise ValueError("overnight panel must match the session panel")
    for t, w in targets.items():
        if type(t) is not int or not 0 <= t < n or not _valid_target(w,names):
            raise ValueError("invalid target date, instrument or long-only weight")
    fee_rate = cost_bps / 10_000
    cash, nav = float(initial_nav), float(initial_nav)
    pos = dict.fromkeys(assets, 0.0)
    rows, fills = [], []
    marks = [] if track_attribution else None
    for t, day in enumerate(returns, 1):
        if set(day) != names or any(not isfinite(x) or x <= -1 for x in day.values()):
            raise ValueError("invalid or missing asset return")
        prior_nav = nav
        buys = sells = fees = 0.0
        target = targets.get(t - 1)
        fee_by_asset = dict.fromkeys(assets,0.) if track_attribution else None
        if target_policy is not None:
            target = target_policy(t-1, prior_nav, None if target is None else dict(target))
            if target is not None and not _valid_target(target,names):
                raise ValueError("policy returned invalid long-only weights")
        gap_pnl = None
        if overnight is not None:
            gap = overnight[t-1]
            if set(gap) != names or any(not isfinite(x) or x <= -1 for x in gap.values()):
                raise ValueError("invalid or missing overnight return")
            gap_pnl = {a:pos[a]*gap[a] for a in assets}
            pos = {a:pos[a]+gap_pnl[a] for a in assets}
            nav = cash + fsum(pos.values())
        nav_at_open = nav
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
                    if track_attribution:
                        fee_by_asset[a] = fill_fee
            cash -= buys - sells + fees
            if not abs(cash - free_nav * (1 - weights_sum)) < 1e-9 * nav_at_open:
                raise ArithmeticError("cash must fund trades and fees")
            cash = max(cash, 0.0)
            pos = next_pos
        if track_attribution:
            overnight_marks = gap_pnl if gap_pnl is not None else dict.fromkeys(assets,0.)
            marks.append({a:AssetMark(pos[a]*day[a]+overnight_marks[a],
                                      fee_by_asset[a],overnight_marks[a]) for a in assets})
        pos = {a: pos[a] * (1 + day[a]) for a in assets}
        nav = cash + fsum(pos.values())
        if not isfinite(nav) or nav <= 0:
            raise ArithmeticError("insolvency or nonfinite equity")
        rows.append(Session(t, nav, cash, nav / prior_nav - 1, fees, buys, sells,
                            (buys + sells) / nav_at_open))
    return Run(float(initial_nav), rows, fills, marks)
