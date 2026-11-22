# 数据可视化与金融图表

这些工具负责画数据。净值、回撤、收益和指标应由已对账的记录导出。 资料核对：2026-11-22。评测状态 `UNMEASURED`。

| 工具与上游 | 用途 | 开用前先查 |
| --- | --- | --- |
| [Matplotlib](https://github.com/matplotlib/matplotlib) | 静态报告、多面板及误差带 | 固定字号、字体、轴与导出大小，避免靠裁轴制造效果。 |
| [Plotly.py](https://github.com/plotly/plotly.py) | 交互净值、回撤、散点和时间序列 | 注明时区、频率和缺失处理；不要在 HTML 打包受限数据。 |
| [Vega-Altair](https://github.com/vega/altair) | Python 声明式统计图、分层筛选 | 明确聚合粒度与抽样步骤。 |
| [Bokeh](https://github.com/bokeh/bokeh) | Python 交互图和联动选择 | 区分单文件示例和运行服务；服务部署不在目录范围。 |
| [Apache ECharts](https://github.com/apache/echarts) | Web dashboard、异动/分层回测面板 | 载入真实图表前确认来源和输出数据边界。 |
| [D3](https://github.com/d3/d3) | 自定义 SVG、Canvas、交互与坐标映射 | 设计成本高，先确定信息结构再写自定义交互。 |
| [Lightweight Charts](https://github.com/tradingview/lightweight-charts) | 浏览器 K 线、成交量、指标叠加 | 图表库不提供行情授权或交易撮合。 |
| [mplfinance](https://github.com/matplotlib/mplfinance) | OHLC、成交量和回测标记的静态金融图 | 别把信号时点和成交时点用同一标记。 |
| [Datashader](https://github.com/holoviz/datashader) | 大量点的栅格聚合和密度视图 | 聚合图不再保留每笔事件身份；注明聚合方式。 |

[回到工具索引](README.md) · [目录入库标准](../CONTRIBUTING.md)
