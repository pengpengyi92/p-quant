# 量化回测研究论文

**作者：Pengyi Peng｜核对时间：2026-11-22T15:35:56+08:00（Asia/Shanghai）**。链接指向原始论文、作者稿或出版社；不复制全文。

| 主题 | 一手出处 | 读它时问什么 |
| --- | --- | --- |
| 回测过拟合的概率 | [Bailey 等，The Probability of Backtest Overfitting](https://escholarship.org/uc/item/4w1110bb) | 选了许多候选后，样本内赢家在外部样本的排名有多不稳定？ |
| 数据反复试探 | [White，A Reality Check for Data Snooping](https://doi.org/10.1111/1468-0262.00152) · [学术存档全文](https://users.ssc.wisc.edu/~behansen/718/White2000.pdf) | 在一个搜索过很多规则的集合里，如何解释最好结果？ |
| 模型选择偏差 | [Cawley 与 Talbot，On Over-fitting in Model Selection](https://www.jmlr.org/papers/v11/cawley10a.html) | 调参评分自身会不会过拟合，最终评估如何独立？ |
| 多因子试验 | [Harvey、Liu 与 Zhu，... and the Cross-Section of Expected Returns](https://doi.org/10.1093/rfs/hhv059) · [NBER 作者稿](https://www.nber.org/system/files/working_papers/w20592/w20592.pdf) | 做过许多因子检验后，单个显著结果该怎么解读？ |
| 波动基线 | [Corsi，A Simple Approximate Long-Memory Model of Realized Volatility](https://doi.org/10.1093/jjfinec/nbp001) · [大学档案](https://iris.unive.it/handle/10278/38476) | 不同时间尺度的历史已实现波动怎样形成可解释的 HAR 基线？ |
| 波动预测损失 | [Patton，Volatility Forecast Comparison Using Imperfect Volatility Proxies](https://public.econ.duke.edu/~ap172/Patton_vol_proxies_JoE_2011.pdf) | 波动代理有误差时，哪些损失函数下比较仍有解释力？ |

策略收益、因子预测和方差预测是不同目标；统计修正不能修掉时间泄漏、成本或执行设定差异。
