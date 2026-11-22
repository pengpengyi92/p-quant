# 向 p-quant 添加资料

先确认项目的官方仓、官方文档或作者版本。使用[入库模板](template/tool-intake.md)，记录用途、语言/运行条件、官方来源、许可证核对状态和与同类工具的边界。找到同名条目时补来源，不创建重复条目；工具条目同时维护分类页与 [catalog.json](repo/catalog.json)。

报告写明 Title、Timestamp（含时区）、Author、输入、基线、协议、结果和失败例。只读了文档写 `UPSTREAM_CHECKED`；实际没有运行的速度、准确度或策略表现写 `UNMEASURED`。不要把 README 宣传、不同环境的榜单或另一个项目的收益当成自己的测量。

只提交自写内容和在公开渠道可再分发的材料。没有许可时只链接，不镜像第三方仓库、文章、数据和报告。禁止提交凭证、未公开个人资料、私有工作区文件和受限行情。工具条目不授予任何数据、软件、券商或交易权利。

在仓库根目录运行 `python scripts/validate_catalog.py` 和 `python -m unittest discover -s tests -v`，校验目录、链接、元数据和合成夹具；这不是第三方引擎实测。
