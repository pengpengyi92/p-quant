# p-quant 下一步

- [x] P0：建立公开的工具、讨论、论文、报告、项目、示例与模板目录；校验首批 41 个官方入口的索引。
- [x] P0：[跑通回测 → 指标 → 绘图](project/pwol-synthetic-demo/README.md)，用冻结合成输入复跑核验，不接行情或交易。
- [x] P1：[新增合成基准和未按收益校准的下跌压力](project/pwol-benchmark-stress/README.md)，完成相对指标与绘图，保留跑输结果。
- [x] P1：[冻结三条无拟合路径，回测降仓与板块/行业贡献](project/pwol-drawdown-guard/README.md)。
- [ ] P2：在新合成路径上预置开盘跳空、费用上升和多次切换，各指标重对账；不在已看路径调阈值。
- [ ] P1：加缺损／晚报和两个基准的压力夹具；图与指标须在零收益、缺损输入中一致。
- [ ] P1：用 [同一份合成回测夹具](project/synthetic-backtest-comparison/README.md)实现至少两个适配器；验收现金、持仓、手续费及逐日权益，保留失败例。当前工具执行是 `NOT_RUN`。
- [ ] P1：给新增工具保留固定上游 tag／commit、许可证及数据条件，另记公开 API 的变动。
- [ ] P2：把不同订单粒度的协议分成 bar 和 L2 两条线；在合法的合成回放上比较缺失、坏序和确定性。
