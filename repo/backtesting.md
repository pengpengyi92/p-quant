# 量化回测与市场仿真

按输入粒度和成交机制分类；列出工程入口不等于测过性能、能离线安装、或适合实盘。 资料核对：2026-11-22。评测状态 `UNMEASURED`。

| 工具与上游 | 用途 | 开用前先查 |
| --- | --- | --- |
| [vectorbt](https://github.com/polakowo/vectorbt) | 向量化／数组研究，批量信号与组合探索 | 资金共享、同一时刻处理顺序、成交延迟与前视风险必须对齐。 |
| [backtesting.py](https://github.com/kernc/backtesting.py) | 轻量 OHLC 策略回测和可读的执行原型 | 先核对 `trade_on_close`、费用、价差和订单语义。 |
| [bt](https://github.com/pmorissette/bt) | 规则驱动的组合配置与再平衡 | 先区分持仓权重回测和逐单成交仿真。 |
| [Backtrader](https://github.com/mementum/backtrader) | 事件驱动的策略/数据/经纪模拟接口 | 接入前验证依赖兼容和当前维护，不推定成交模型适配自己。 |
| [Zipline Reloaded](https://github.com/stefan-jansen/zipline-reloaded) | 事件式日频／分钟研究、交易日历与数据 bundle | 核对历史成份、公司行动、bundle 与资产日历。 |
| [LEAN](https://github.com/QuantConnect/Lean) | 事件驱动引擎，Python／C#，多资产研究入口 | 引擎公开不等于托管、历史数据或券商连接免费或有授权。 |
| [NautilusTrader](https://github.com/nautechsystems/nautilus_trader) | 事件驱动市场数据与订单模拟，Python／Rust | 先比较模型的延迟、手续费、订单簿输入与同时间顺序。 |
| [HftBacktest](https://github.com/nkaz001/hftbacktest) | 盘口回放、排队和延迟建模 | 排队、冲击、隐性流动性都受数据与仿真假设限制；不能由 bar 反推。 |
| [Microsoft Qlib](https://github.com/microsoft/qlib) | 数据、特征、模型、策略、回测串联的研究框架 | 先核对样本划分、标签窗口、历史成份；不把发布的数据说明等同再分发权。 |
| [PyBroker](https://github.com/edtechre/pybroker) | Python 策略研究、模型集成与 walk-forward | 严格核对每次训练使用的标签/窗口，不能先看测试再调参。 |
| [Freqtrade](https://github.com/freqtrade/freqtrade) | 加密策略工具，含回测和偏差分析入口 | 仅研究目录，不能启用交易；注意 OHLC 内成交假设。 |
| [RQAlpha](https://github.com/ricequant/rqalpha) | 可扩展的回测框架，适合研究其中国市场生态 | 行情 bundle、历史规则与数据授权单独核实。 |
| [VeighNa / vn.py](https://github.com/vnpy/vnpy) | 模块化量化交易框架；另有官方 [CTA 回测模块](https://github.com/vnpy/vnpy_ctabacktester) | 交易框架不等于数据源；区分 CTA 模块、模拟和网关行为。 |

[回到工具索引](README.md) · [目录入库标准](../CONTRIBUTING.md)
