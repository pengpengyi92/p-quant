# 公众目录与回测一致性基准

**作者：Pengyi Peng｜时间：2026-11-22T15:35:56+08:00（Asia/Shanghai）**

| Baseline | Change | Measure | Result | Trade-off | Next Action |
| --- | --- | --- | --- | --- | --- |
| 手算订单与现金流水 | 引入两个或更多离线引擎的合成适配 | 成交日、成交价、费用、现金、持仓与权益逐项一致 | 外部引擎 `UNMEASURED`；独立合成账本预期值可复算 | 引擎默认规则不一样；先校准再比，禁止默默采用不同口径 | 完成 [固定合成协议](project/synthetic-backtest-comparison/README.md)，保留未通过的设置差异 |
| 手工散落的工具链接 | 用分类目录加机器可读登记 | ID 唯一、URL 属于官方入口、分类页覆盖、报告元数据 | 由仓库校验脚本测试，链接的可用性是核对时点的观察 | 不是全网穷举，也不是维护度排名 | 新增条目记录版本、许可、验证范围 |
| 手画图或不可编辑截图 | 研究流程用 Mermaid 示例并保留代码 | 时点、数据、订单和对账分支是否明确 | 示例已写；导出体积和不同渲染器表现 `UNMEASURED` | 老渲染器可能解析不同，源文件与说明一起维护 | GitHub 中按[官方文档](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)查看源码渲染 |
