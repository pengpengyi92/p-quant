# pdrawer 量化绘图

pdrawer 只画已经算好的结果，不改账本、不重新拟合指标。读取同一运行目录里的 `summary.json` 与 `series.json`，先核对 NAV 和最大回撤，再画四个视图：费后净值、回撤、分调仓期收益及双边换手。图注明频率、费用、时间和数据性质。

[看 PWOL 风格合成演示图](../project/pwol-synthetic-demo/artifacts/pwol-synthetic-dashboard.svg)

Python 3.12 环境（系统不必有图形界面），在仓库根运行：

```bash
python -m pip install -r pdrawer/requirements.txt
python -B -m pdrawer.dashboard --run project/pwol-synthetic-demo/artifacts --output .local/pwol-dashboard
```

默认输出 SVG 和 PNG；只要某一格式可指定 `--format svg` 或 `--format png`。输出文件名若已存在则拒绝覆盖。下一步：保留此读输出接口，再加基准曲线、因子暴露及归因图；未提供基准时不凭空补对照。
