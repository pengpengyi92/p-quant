# 绩效、因子与组合优化

这些是指标、因子诊断和组合优化入口，不自带历史成交。 资料核对：2026-11-22。评测状态 `UNMEASURED`。

| 工具与上游 | 用途 | 开用前先查 |
| --- | --- | --- |
| [QuantStats](https://github.com/ranaroussi/quantstats) | 收益序列统计和报告 | 统一净／毛收益、时区、年化、基准和缺失日。 |
| [Pyfolio Reloaded](https://github.com/stefan-jansen/pyfolio-reloaded) | 绩效和风险归因图表 | 输入收益、交易、净值的频率与单位必须匹配。 |
| [Empyrical Reloaded](https://github.com/stefan-jansen/empyrical-reloaded) | 金融风险和收益指标函数 | 与独立对照一起检验极端值、年化频率和零分母。 |
| [Alphalens Reloaded](https://github.com/stefan-jansen/alphalens-reloaded) | 前向收益与因子 IC／分桶诊断 | 检查时间可用性、行业／规模暴露、幸存者与重叠标签。 |
| [PyPortfolioOpt](https://github.com/PyPortfolio/PyPortfolioOpt) | 均值方差、Black–Litterman、分层风险平价等组合方法 | 回测中对齐估计窗、换手和成本，不把优化目标当真实结果。 |
| [CVXPY](https://github.com/cvxpy/cvxpy) | 凸优化和组合约束表达 | 记求解器、容差、可行性和失败状态。 |
| [Riskfolio-Lib](https://github.com/dcajasn/Riskfolio-Lib) | 多风险模型的组合优化和比较 | 风险定义、估计区间、约束及下一交易时点要单独记录。 |

[回到工具索引](README.md) · [目录入库标准](../CONTRIBUTING.md)
