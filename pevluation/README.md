# pevluation 组合评估计算

按指定的目录名 `pevluation` 维护指标定义和计算。`metrics.evaluate` 从净回报、NAV 和成交账本得出结果；图表读这些结果，不再实现另一套 Sharpe 或回撤公式。

| 指标组 | 字段 | 口径 |
| --- | --- | --- |
| 收益 | `total_return`、`cagr` | 日净收益复利；CAGR 按观测期数和一年期数指数化。本样本正好 252 期，所以两个数相同。 |
| 波动与 Sharpe | `annual_volatility`、`sharpe` | 年化频率 252；样本标准差乘 √252。Sharpe 为日均超额收益除以日样本标准差再乘 √252；年无风险转日复利，示例取 0%。 |
| 下行与回撤 | `sortino`、`max_drawdown`、`longest_underwater_sessions`、`calmar` | Sortino 用全样本中负超额收益的均方根；回撤 = NAV／运行峰值 − 1，峰值纳入期初 NAV；未恢复到峰值的最长连续期；Calmar = CAGR／最大回撤绝对值。 |
| 胜率和极值 | `win_rate`、`daily_profit_factor`、`best_session_return`、`worst_session_return` | 正收益日比例、正日收益总和／负日收益绝对值总和、单日最高／最低净回报。利润因子是日频，不是逐交易胜率。 |
| 换手 | `gross_turnover_including_open`、`gross_turnover_excluding_open`、`half_gross_turnover_excluding_open`、`initial_deployment_turnover` | 每期双边买卖金额和／成交前 NAV 再加总；期初从现金建仓独立列示。半双边是双边除以 2 的另一个口径，不和双边混用。 |
| 费用与活动 | `total_fees`、`fees_pct_initial_nav`、`fills`、`rebalance_sessions_including_open` | 成交费用求和及相对期初 NAV、成交笔数、实际有换手的期数。 |
| 样本和假设 | `initial_nav`、`ending_nav`、`sessions`、`periods_per_year`、`risk_free_annual` | 保留年化参数和样本口径，便于审计重算。 |

分母为零而无定义的比率返回 `null`，不填 0 或∞。回撤是按期收盘计算，不代表盘中峰谷。本演示没有真实基准、因子暴露或成交概率，不补 Alpha、Beta、IR 或策略评级；也不把 Sharpe 校准当实证。

[本轮机器可读指标](../project/pwol-synthetic-demo/artifacts/summary.json) · [运行说明](../project/pwol-synthetic-demo/README.md)
