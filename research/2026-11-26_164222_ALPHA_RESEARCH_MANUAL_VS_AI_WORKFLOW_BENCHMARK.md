# Manual vs Scripted vs AI-Assisted Alpha Research — Open Benchmark Protocol

**Title:** Quant Research Workflow: Manual Baseline × Scripted Automation × AI Assistance
**Timestamp:** 2026-11-26T16:42:22+08:00 (Asia/Shanghai)
**Owner:** Pengyi Peng
**Repository:** pengpengyi92/p-quant
**Visibility:** PUBLIC
**Status:** PROPOSED / NOT_RUN / NO_MEASURED_SPEEDUP / EDUCATIONAL
**Evidence policy:** This is a general, publicly shareable experimental design with no private employment, banking, individual performance, privileged data, real strategy, or identity-dependent claims.

## Research question
Does AI-assisted quantitative research create **more valid, reproducible out-of-sample hypotheses per unit researcher time and compute cost** than (A) manual exploration or (B) conventional scripted automation? Does any productivity gain survive robust selection-bias and realistic net-of-costs tests?

## Experimental arms
1. **Manual / A**: A researcher reads selected permitted materials, proposes expressions, and manually tests candidates with a frozen testing harness.
2. **Scripted / B**: Fixed-code rule-based generation or factor-screening system using the same materials, compute cap, candidate budget and harness.
3. **AI-assisted / C**: An LLM or agent proposes hypotheses and code within a predefined budget; human approval, schema checks and independent evaluation are retained.

## Fair comparison protocol
- Use solely public or synthetic data with stated redistribution rights. Freeze data download date, symbols, calendar, split boundaries, pricing and corporate actions.
- Fix candidate search budget, human time, GPU/CPU time, prompting/token cost, baseline, random seeds and all preprocessing.
- Pre-register acceptance rules for formula validity, point-in-time availability, train/validation/test separation and maximum search attempts.
- Keep immutable experiment manifests for all candidates, including negative results and invalid outputs. Avoid post hoc winner selection.
- Use chronological and walk-forward out-of-sample tests, realistic fees/slippage/turnover assumptions and stress regimes. Performance is a simulation, not a live-fund result.
- Report the **entire** distribution and uncertainty; do not cherry-pick alpha examples or make unsupported causal claims about research skill.

## Scorecard
| Metric | Definition | Status |
| --- | --- | --- |
| Valid hypotheses / researcher hour | Number of candidate strategies passing syntax, compliance and point-in-time gates per active researcher hour | UNMEASURED |
| Reproduction pass rate | Fraction re-runnable from documented data and dependency manifest | UNMEASURED |
| Data leakage / error rate | Number of lookahead, survivorship and label leakage failures | UNMEASURED |
| OOS performance | Distribution of strictly out-of-sample risk-adjusted returns after costs, not just max-selected Sharpe | UNMEASURED |
| Capacity sensitivity | Stress execution assumptions and estimated turnover/impact | UNMEASURED |
| AI/Compute cost | Token, GPU, CPU, cloud and human review cost per valid hypothesis | UNMEASURED |
| Realized net P&L | Requires separately authorized live trading and auditable records | NOT_APPLICABLE |

## Expected failure cases
- AI produces convincing but impossible or future-looking features.
- Scripted generators search huge spaces and inflate false discovery.
- Human manual baseline is unfairly given different information or time.
- Faster hypothesis generation increases overfitting instead of usable signal.
- Backtest success disappears after execution-cost and regime changes.

## Design boundary
AI productivity multipliers (e.g., 3×, 5× or 10×) are **hypotheses, not observations**. The protocol has no run data. The experiment does not provide real orders, brokerage access, restricted market data or investment advice.

## Related open research paths
- [Project index](../project/README.md)
- [Evaluation index](../pevluation/README.md)
- [Backtest index](../pbacktest/README.md)
- [Contributing and evidence standards](../CONTRIBUTING.md)

No private cross-repository links are included because this is a public technical knowledge repository.
