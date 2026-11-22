# pdrawer 量化绘图

[三版降仓对照图](../project/pwol-tiered-drawdown/README.md)：同尺度比较净值、回撤和目标仓位，标明冲击与隔夜跳空。

pdrawer 只画已经算好的结果，不改账本、不重新拟合指标。读取同一运行目录里的 `summary.json` 与 `series.json`，先核对 NAV 和最大回撤，再画四个视图：费后净值、回撤、分调仓期收益及双边换手。图注明频率、费用、时间和数据性质。

[看 PWOL 风格合成演示图](../project/pwol-synthetic-demo/artifacts/pwol-synthetic-dashboard.svg)

[看合成基准和下跌压力的净值／回撤同刻度图](../project/pwol-benchmark-stress/artifacts/comparison.svg)。`python -m pdrawer.benchmark --run <结果目录> --output <图文件前缀>` 从两套已对账的轨迹画对照，不重新算统计量。

[看三种路径的回撤降仓图](../project/pwol-drawdown-guard/artifacts/comparison.svg)。`python -m pdrawer.drawdown_guard` 读取同一实验的净值、回撤和目标仓位，标出固定冲击段，所有列共用刻度。

Python 3.12 环境（系统不必有图形界面），在仓库根运行：

```bash
python -m pip install -r pdrawer/requirements.txt
python -B -m pdrawer.dashboard --run project/pwol-synthetic-demo/artifacts --output .local/pwol-dashboard
```

默认输出 SVG 和 PNG；只要某一格式可指定 `--format svg` 或 `--format png`。输出文件名若已存在则拒绝覆盖。下一步：保留此读输出接口，再加基准曲线、因子暴露及归因图；未提供基准时不凭空补对照。
