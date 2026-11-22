# 回测流程图示例

把信号和成交拆成不同节点。不画出这条时间边界，回测很难从图上审查是否用了未来数据。GitHub 支持用 [Mermaid 源码](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)渲染如下流程。

```mermaid
flowchart LR
    A["时点 t：数据已可用"] --> B["冻结信号和目标持仓"]
    B --> C["时点 t+1：模拟开盘成交"]
    C --> D["记录成交价、费用与现金"]
    D --> E["期末盯市及独立对账"]
    E --> F{"账本通过？"}
    F -- "是" --> G["再画净值和回撤"]
    F -- "否" --> H["记录失败，停止比较"]
```

对应 [合成订单账本](../project/synthetic-backtest-comparison/README.md)；图不是交易引擎。
