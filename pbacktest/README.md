# pbacktest 回测账本

[分档降仓](../project/pwol-tiered-drawdown/README.md)增加可选隔夜收益面板：先用上一收盘生成目标，随后先给旧持仓记跳空、再按新开盘账本撮合、扣费并记盘中损益。未传面板时保留原来的无跳空行为。

`engine.run_backtest` 吃一个按时点排序的资产收益面板和目标权重序列，输出独立的日度 NAV 与成交账本。上一期收盘给出目标，下一期虚拟开盘先成交及扣费，再按当期收益盯市。使用分数持仓、长仓与现金限额；默认用合成 no-gap 开盘，不接行情、订单簿或券商。

[PWOL 风格合成小样](../project/pwol-synthetic-demo/README.md)展示 21 期一调。发动机先求出扣费后的可投资金额，再按权重下单，所以交易和费用都由现金与卖出所得承担。改当期价格回报不会改变当期开盘成交；测试有专门用例。

从仓库根目录运行（Python 3.12，标准库即可）：

```bash
python -B -m pbacktest.pwol_demo --output .local/pwol-run
```

日账本和成交账本都是模拟产物。未来接入其他引擎前先验价格、可用时点、费用、成交的逐笔口径，不默认横向可比。

用 `python -m pbacktest.pwol_benchmark_stress --output .local/pwol-benchmark-replay` 跑两个合成情景：[给原组合加基准，以及固定冲击下的独立压力](../project/pwol-benchmark-stress/README.md)。后者沿用相同的账本引擎和权重，但完全不拟合收益。

[三条路径的降仓工具](../project/pwol-drawdown-guard/README.md)在引擎增加可选 prior-close policy 与资产盈亏标记；未开启时保留旧账本口径。
