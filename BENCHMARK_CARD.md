# 公众目录与回测一致性基准

## 合成组合绘图与指标链

[回撤降仓三路径](project/pwol-drawdown-guard/README.md)：Baseline 为同资产不降仓，Change 为仅看过去的风险开关，Measure 为同基准 MDD、跌后净收益及可对账行业贡献，Result 为 V 形少回撤 6.96 pp、少赚 19.15 pp。Trade-off：持续低仓位可挡后续跌幅，也能错过快速恢复。Next Action：在新数据测跳空和反复切换；真实效果 UNMEASURED。

[合成基准及未校准压力](project/pwol-benchmark-stress/README.md)：Baseline 是同情景合成指数；Change 是匹配期次的超额、Alpha/Beta、IR 与各自回撤；Measure 使用公式单测和同刻度轨迹；Result 是未校准压力组合亏损 24.96%，落后基准 3.18 个百分点。Trade-off：固定合成机制，不衡量真实风险或收益；Next Action：冻结缺损及多压力路径。

[同一合成账本](project/pwol-synthetic-demo/README.md)：Baseline 为手算费用与时点，Change 为可复算回测、指标矩阵、静态渲染；Measure 为 NAV、交易与输出哈希，Result 为 3 次数字及 2 次 SVG 同环境复跑一致。Trade-off：上调路径只用于演示，不能检验市场预测。Next Action：锁定不按收益校准的压力路径和独立引擎再验；真实表现 UNMEASURED。

**作者：Pengyi Peng｜时间：2026-11-22T15:35:56+08:00（Asia/Shanghai）**

| Baseline | Change | Measure | Result | Trade-off | Next Action |
| --- | --- | --- | --- | --- | --- |
| 手算订单与现金流水 | 引入两个或更多离线引擎的合成适配 | 成交日、成交价、费用、现金、持仓与权益逐项一致 | 外部引擎 `UNMEASURED`；独立合成账本预期值可复算 | 引擎默认规则不一样；先校准再比，禁止默默采用不同口径 | 完成 [固定合成协议](project/synthetic-backtest-comparison/README.md)，保留未通过的设置差异 |
| 手工散落的工具链接 | 用分类目录加机器可读登记 | ID 唯一、URL 属于官方入口、分类页覆盖、报告元数据 | 由仓库校验脚本测试，链接的可用性是核对时点的观察 | 不是全网穷举，也不是维护度排名 | 新增条目记录版本、许可、验证范围 |
| 手画图或不可编辑截图 | 研究流程用 Mermaid 示例并保留代码 | 时点、数据、订单和对账分支是否明确 | 示例已写；导出体积和不同渲染器表现 `UNMEASURED` | 老渲染器可能解析不同，源文件与说明一起维护 | GitHub 中按[官方文档](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)查看源码渲染 |
