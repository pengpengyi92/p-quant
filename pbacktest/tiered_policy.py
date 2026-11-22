"""Deterministic drawdown state machine; no price or scenario feed."""
from dataclasses import asdict
from math import isfinite

from pbacktest.drawdown_policy import Decision


class TieredDrawdownPolicy:
    def __init__(self, initial_nav, *, exposures, enter, exit, min_completed, confirm_closes):
        if (not isfinite(initial_nav) or initial_nav <= 0 or len(exposures) < 2
                or len(enter) != len(exposures)-1 or len(exit) != len(enter)
                or exposures[0] != 1 or not all(0 < b < a for a,b in zip(exposures,exposures[1:]))
                or not all(0 < a < b < 1 for a,b in zip(exit,enter))
                or not all(a < b for xs in (enter,exit) for a,b in zip(xs,xs[1:]))
                or any(type(n) is not int or n < 1 for n in (min_completed,confirm_closes))):
            raise ValueError("invalid tiered rule")
        self.exposures, self.enter, self.exit = tuple(exposures), tuple(enter), tuple(exit)
        self.min_completed, self.confirm_closes = min_completed, confirm_closes
        self.tier, self.last, self.changed, self.confirmed = 0, -1, None, 0
        self.peak, self.base, self.trace = initial_nav, None, []

    def __call__(self, t, close_nav, scheduled):
        if t != self.last+1 or not isfinite(close_nav) or close_nav <= 0:
            raise ValueError("one sequential, known close is required")
        self.last = t
        self.peak = max(self.peak,close_nav)
        depth = 1-close_nav/self.peak
        if scheduled is not None:
            self.base = dict(scheduled)
        if self.base is None:
            raise ValueError("missing initial target weights")
        depth_tier = sum(depth >= x-1e-12 for x in self.enter)
        action = "hold"
        if depth_tier > self.tier:
            self.tier = depth_tier
            action = "reduce"
        elif self.tier > 0:
            self.confirmed = self.confirmed+1 if depth <= self.exit[self.tier-1]+1e-12 else 0
            if t-self.changed >= self.min_completed and self.confirmed >= self.confirm_closes:
                self.tier -= 1
                action = "restore_one"
        if action != "hold":
            self.changed, self.confirmed = t, 0
        exposure = self.exposures[self.tier]
        self.trace.append(Decision(t,t+1,close_nav,self.peak,-depth,exposure,action,scheduled is not None))
        if scheduled is not None or action != "hold":
            return {a:exposure*w for a,w in self.base.items()}
        return None

    def switches(self):
        return [asdict(x) for x in self.trace if x.action != "hold"]
