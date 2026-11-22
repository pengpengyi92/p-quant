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

## 有基准时的相对绩效矩阵

`relative.compare_matched_returns` 只接受两边完全匹配且连续的期次；拒绝缺日期、错位，不自动补零。默认 252 期年化、无风险年利率 0。没有真实基准时，可以给出明确标记的合成基准进行压力比较。

| 相对指标 | 计算口径 |
| --- | --- |
| 累计超额（pp） | 组合累计净收益 − 基准累计收益，再换作百分点。 |
| 相对累计复利 | 两条从 1 起步的终点净值比 − 1；一般不等于百分点之差。 |
| 年化主动收益、跟踪误差、IR | 用同期日收益差。日均主动收益 × 252；日样本标准差 × √252；IR = 两者之比。跟踪误差为零时 IR 为 `null`。 |
| OLS Alpha 和 Beta | 组合日超额收益回归基准日超额收益，Beta 为协方差／基准方差；日截距 × 252 得算术年化 Alpha。基准无波动时二者为 `null`。 |
| 组合／基准／相对回撤 | 分别对组合净值、基准净值和两者的净值比，从自己的峰值（含起点）量最大下探。 |

[合成基准和未校准下跌验收](../project/pwol-benchmark-stress/README.md) · [完整指标矩阵](../report/2026-11-22-pwol-benchmark-and-stress.md)

## Sector 与 industry 对账

`attribution.partition_contributions` 按资产聚合当期仓位产生的毛损益，减去该资产自己的费用，再用窗口起始 NAV 归一。所有 sector 的贡献和、所有 industry 的贡献和分别等于组合净收益；这是贡献，不是行业独立收益。`guard_effects` 区分最大回撤改善、期末累计差与固定跌后窗口的收益差。[三路径例子](../project/pwol-drawdown-guard/README.md)
