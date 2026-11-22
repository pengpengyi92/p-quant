"""Precommitted comparison of protection and fee-inclusive recovery."""


def review_tiers(metrics, window, minimum_share):
    original, binary, tiered = (metrics[k] for k in ("original","binary","tiered"))
    binary_saved = 100*(binary["max_drawdown"]-original["max_drawdown"])
    tiered_saved = 100*(tiered["max_drawdown"]-original["max_drawdown"])
    rebound_gain = 100*(window["tiered"]-window["binary"])
    protected = tiered_saved > 1e-10 and tiered_saved+1e-10 >= max(binary_saved,0)*minimum_share
    recovered = rebound_gain > 1e-10
    return {
        "binary_drawdown_saved_pp":binary_saved,
        "tiered_drawdown_saved_pp":tiered_saved,
        "retained_fraction_of_positive_binary_improvement":tiered_saved/binary_saved if binary_saved>1e-10 else None,
        "tiered_minus_binary_window_net_pp":rebound_gain,
        "tiered_minus_binary_terminal_net_pp":100*(tiered["total_return"]-binary["total_return"]),
        "tiered_minus_binary_turnover_pp":100*(tiered["gross_turnover_excluding_open"]-binary["gross_turnover_excluding_open"]),
        "tiered_minus_binary_fee_bps_initial_nav":10000*(tiered["fees_pct_initial_nav"]-binary["fees_pct_initial_nav"]),
        "passes_drawdown_gate":protected,
        "passes_rebound_gate":recovered,
        "passes_joint_gate":protected and recovered,
    }
