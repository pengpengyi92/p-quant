# 流程图与架构图

用来画研究流程、状态或系统关系，不用来计算收益、模拟成交。 资料核对：2026-11-22。评测状态 `UNMEASURED`。

| 工具与上游 | 用途 | 开用前先查 |
| --- | --- | --- |
| [Mermaid](https://github.com/mermaid-js/mermaid) | Markdown 原生流程图、时序图 | 先验证目标渲染器支持的语法；图源与文字说明一起保留。 |
| [D2](https://github.com/d2lang/d2) | 文本到架构图，适合从代码维护布局 | 需要独立渲染，固定引擎版本和导出格式。 |
| [Graphviz](https://gitlab.com/graphviz/graphviz) | DOT 关系图、依赖拓扑、DAG | 密图的可读性要抽样看，不把依赖箭头画成因果。 |
| [PlantUML](https://github.com/plantuml/plantuml) | UML 序列图、活动图和组件图 | 选择实际 IDE 或离线渲染路径，不把内部图文本传给公共渲染服务。 |
| [diagrams.net / draw.io](https://github.com/jgraph/drawio) | 手工拖拽，协作梳理系统 | 提交源文件加 SVG/PNG；不只收不可编辑截图。 |
| [Excalidraw](https://github.com/excalidraw/excalidraw) | 白板和初步方案草图 | 正式文档中另写节点含义和决策依据。 |
| [C4-PlantUML](https://github.com/plantuml-stdlib/C4-PlantUML) | C4 的系统、容器和组件视图 | 离线渲染时固定所引图元，避免漂移。 |
| [Structurizr DSL](https://docs.structurizr.com/dsl) | 同一架构模型表达多种 C4 视图 | 此项收录官方 DSL 文档，不暗示托管功能、账号权限或许可。 |

[回到工具索引](README.md) · [目录入库标准](../CONTRIBUTING.md)
