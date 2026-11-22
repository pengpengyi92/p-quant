# 流程图、图表和量化回测工具怎么选

**作者：Pengyi Peng｜时间：2026-11-22T15:35:56+08:00（Asia/Shanghai）**

入门组合：**Mermaid 画流程，Matplotlib 或 Plotly 画结果，vectorbt 做批量假设筛选，再用一个独立事件引擎核对少量订单。** 若问题是盘口排队和延迟，一开始就需要盘口事件和明确的撮合假设，不能靠 bar 回测近似一个自己没观察到的成交。

| 任务 | 建议先看 | 再问什么 |
| --- | --- | --- |
| 写 README、评审策略路径和事件顺序 | [Mermaid](https://github.com/mermaid-js/mermaid)，可编辑的白板备选 [draw.io](https://github.com/jgraph/drawio) 或 [Excalidraw](https://github.com/excalidraw/excalidraw) | 图能否同时说清数据可用、决策、成交与对账？按[GitHub 的 Mermaid 文档](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)嵌入。 |
| 报告净值、回撤、成交表 | [Matplotlib](https://github.com/matplotlib/matplotlib) 固定报告；[Plotly](https://github.com/plotly/plotly.py) 交互比较；[Lightweight Charts](https://github.com/tradingview/lightweight-charts) 浏览器 K 线 | 先确认收益净毛、价格单位、现金和权益；图上标记决策和成交是两个事件。 |
| 批量筛假设或做组合配置 | [vectorbt](https://github.com/polakowo/vectorbt) 做数组或参数探索；[bt](https://github.com/pmorissette/bt) 看组合再平衡 | 参数越多，越要留出独立验证、记录搜索空间；同一根 K 线上的执行顺序要明示。 |
| 把信号落为可对账的订单 | [backtesting.py](https://github.com/kernc/backtesting.py) 做小型 bar 对照；[NautilusTrader](https://github.com/nautechsystems/nautilus_trader) 或 [LEAN](https://github.com/QuantConnect/Lean) 读事件执行 | 理解订单可用时间、分笔成交、取消、手续费、持仓和现金，不强行宣称多个引擎同口径。 |
| 排队、延迟和盘口回放 | [HftBacktest](https://github.com/nkaz001/hftbacktest) | 模拟粒度、重放假设和数据权益首先确认；回放不是市场冲击或实盘承诺。 |

不要先比较哪家年化高。先用[固定合成协议](../project/synthetic-backtest-comparison/README.md)对成交价、时间、费用与账本；结果一致后才比较运行时间、资源、可维护性和更复杂的交易机制。对可用日期、复权、历史成份、成本和复盘结果单独保存证据。此报告是官方文档导读和选型建议，没有运行这些外部工具或排名：`UNMEASURED`。

[查看全部 41 个工具](../repo/README.md) · [看一张流程图示例](../example/README.md) · [先读回测论文](../paper/README.md)
