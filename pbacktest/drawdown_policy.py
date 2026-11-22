"""Drawdown rule with hysteresis, operating only on the observed prior close."""
from dataclasses import asdict, dataclass
from math import isfinite


@dataclass(frozen=True)
class Decision:
    decision_session: int
    fill_session: int
    close_nav: float
    peak_nav: float
    observed_drawdown: float
    target_exposure: float
    action: str
    scheduled_rebalance: bool


class DrawdownPolicy:
    def __init__(self, initial_nav, *, reduce_on_drawdown, restore_within_drawdown,
                 reduced_target, minimum_completed_sessions):
        if (not isfinite(initial_nav) or initial_nav <= 0
                or not 0 < restore_within_drawdown < reduce_on_drawdown < 1
                or not 0 < reduced_target < 1
                or type(minimum_completed_sessions) is not int or minimum_completed_sessions < 1):
            raise ValueError("invalid drawdown thresholds/cooldown")
        self.peak = initial_nav
        self.enter_threshold = reduce_on_drawdown
        self.exit_threshold = restore_within_drawdown
        self.reduced_target = reduced_target
        self.cooldown = minimum_completed_sessions
        self.last = -1
        self.reduced_from = None
        self.base = None
        self.trace = []

    def __call__(self, t, close_nav, scheduled):
        if t != self.last+1 or not isfinite(close_nav) or close_nav <= 0:
            raise ValueError("policy requires one sequential, known close NAV")
        self.last = t
        self.peak = max(self.peak,close_nav)
        dd = close_nav/self.peak - 1
        has_schedule = scheduled is not None
        if has_schedule:
            self.base = dict(scheduled)
        if self.base is None:
            raise ValueError("missing initial target weights")
        action = "hold"
        if self.reduced_from is None and -dd >= self.enter_threshold-1e-12:
            self.reduced_from=t
            action="reduce"
        elif (self.reduced_from is not None and t-self.reduced_from>=self.cooldown
              and -dd<=self.exit_threshold+1e-12):
            self.reduced_from=None
            action="restore"
        exposure = self.reduced_target if self.reduced_from is not None else 1.
        self.trace.append(Decision(t,t+1,close_nav,self.peak,dd,exposure,action,has_schedule))
        if has_schedule or action!="hold":
            return {a:exposure*w for a,w in self.base.items()}
        return None

    def switches(self):
        return [asdict(x) for x in self.trace if x.action!="hold"]
