# p-quant

公开的量化研究资源目录：收录画流程图、画研究结果与做量化回测的工具，也收录论文、可复现实验和选型讨论。先按任务找工具，再用同一份测试输入比行为。

| 目录 | 收录内容 |
| --- | --- |
| [repo](repo/README.md) | 图、回测、绩效、优化与研究数据；41 个官方入口 |
| [discussion](discussion/README.md) | 时间、成交和评测口径的公开讨论记录 |
| [paper](paper/README.md) | 回测过拟合、选择偏差与波动评估论文 |
| [report](report/README.md) | 带作者与时间的对比报告 |
| [project](project/README.md) | 可复现实验协议、预期结果和验证 |
| [example](example/README.md) | Mermaid 回测流程图及从图到证据的例子 |
| [template](template/README.md) | 新仓入库与证据字段 |
| [pbacktest](pbacktest/README.md) | 离线回测、成交／费用与 NAV 账本 |
| [pevluation](pevluation/README.md) | 指标计算和评估矩阵 |
| [pdrawer](pdrawer/README.md) | 从实验产物统一绘图与导出 |

[PWOL 风格合成组合示例](project/pwol-synthetic-demo/README.md)：用一次可复跑的月频演示串起三模块。50% 和 Sharpe 5 为校准目标，不代表 PWOL 真实业绩。

[基准与未校准下跌压力](project/pwol-benchmark-stress/README.md)：同样的组合规则在刻意下跌的合成情景里表现更差；净值和回撤均用同刻度对照，指标由 `pevluation` 计算。

**快速开始：**画 GitHub 流程图看 [Mermaid](repo/diagrams.md)，画净值/回撤先看 [Matplotlib 或 Plotly](repo/visualization.md)，想批量研究信号、比事件引擎或核对盘口模拟看 [回测工具目录](repo/backtesting.md)。优先读[首期选型报告](report/2026-11-22-diagram-and-backtesting-tools.md)。

本仓用于公开研究教育与技术索引。只录入上游链接、原创说明和合成例子；不存受限行情、不收私有材料、也不提供交易接入。[贡献方式](CONTRIBUTING.md) · [计划](TODO.md) · [Benchmark Card](BENCHMARK_CARD.md)。
