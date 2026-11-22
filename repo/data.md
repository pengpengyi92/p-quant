# 研究数据与实验表

没有合法、有时间戳的输入，回测没有可解释性。数据工具不等于行情供应商。 资料核对：2026-11-22。评测状态 `UNMEASURED`。

| 工具与上游 | 用途 | 开用前先查 |
| --- | --- | --- |
| [pandas](https://github.com/pandas-dev/pandas) | 时间序列清理、窗口和合并对照 | 先检查时区、排序、重复、缺失和分组边界。 |
| [Polars](https://github.com/pola-rs/polars) | 列式流水线、惰性扫描、时间序列连接 | 核对排序／联接语义和结果，不先拿速度替代正确性。 |
| [DuckDB](https://github.com/duckdb/duckdb) | 在本地 SQL 中查 Parquet、做数据验收 | 明确索引键、时点选择和资源；不可用快照不应回填。 |
| [Apache Arrow](https://github.com/apache/arrow) | 列式交换、时间戳及跨语言研究用数据容器 | 锁 schema 和时间语义；存储格式不改变底层数据授权。 |

[回到工具索引](README.md) · [目录入库标准](../CONTRIBUTING.md)
