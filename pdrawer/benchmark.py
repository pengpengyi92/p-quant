"""Render NAV and drawdown comparisons from a checked synthetic scenario manifest."""
import argparse
import json
from math import isclose, isfinite
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator, MultipleLocator

CASES = ("calibrated","unfitted_stress")


def load_comparison(folder):
    result = json.loads((folder/"summary.json").read_text(encoding="utf-8"))
    series = json.loads((folder/"comparison-series.json").read_text(encoding="utf-8"))
    if (result["scope"] != "SYNTHETIC_ONLY_NO_TRADE" or series["scope"] != result["scope"] or
            result["market_data"] is not False or result["execution_authorized"] is not False):
        raise ValueError("not a synthetic comparison")
    fields = ["session","portfolio_nav","benchmark_nav","relative_nav",
              "portfolio_drawdown","benchmark_drawdown","relative_drawdown"]
    if series["columns"] != fields:
        raise ValueError("wrong comparison schema")
    for case in CASES:
        rows = series["cases"][case]
        m = result["cases"][case]["metrics"]
        if len(rows)!=1+m["observations"] or not all(
                len(r)==len(fields) and r[0]==i and all(isfinite(x) for x in r) for i,r in enumerate(rows)):
            raise ValueError("bad comparison session sequence")
        p,b = rows[-1][1:3]
        if (not isclose(p-1,m["portfolio_total_return"],abs_tol=1e-11)
                or not isclose(b-1,m["benchmark_total_return"],abs_tol=1e-11)
                or not isclose(min(r[4] for r in rows),m["portfolio_max_drawdown"],abs_tol=1e-11)
                or not isclose(min(r[5] for r in rows),m["benchmark_max_drawdown"],abs_tol=1e-11)):
            raise ValueError("line traces do not agree with their summary")
    return result, series["cases"]


def render(folder, stem, formats=("svg","png")):
    result, sets = load_comparison(folder)
    nav = [x for rows in sets.values() for r in rows for x in r[1:3]]
    dd = [x for rows in sets.values() for r in rows for x in r[4:6]]
    navy, amber, ink, muted, grid = "#12628a","#9b4c17","#102b40","#466070","#dce6ed"
    plt.rcParams.update({"font.family":"DejaVu Sans","axes.facecolor":"#fff",
                         "axes.edgecolor":grid,"axes.labelcolor":ink,
                         "xtick.color":muted,"ytick.color":muted,
                         "svg.fonttype":"none","svg.hashsalt":"pdrawer-benchmark-v1"})
    fig, ax = plt.subplots(2,2,figsize=(11.5,7.2),sharex=True,sharey="row",facecolor="white")
    fig.subplots_adjust(left=.10,right=.967,top=.755,bottom=.13,wspace=.12,hspace=.39)
    fig.text(.10,.941,"PWOL-style portfolio vs synthetic benchmark",fontsize=21,color=ink,fontweight="bold")
    fig.text(.10,.904,"SYNTHETIC ONLY  /  NOT ACTUAL PWOL PERFORMANCE",fontsize=10,color=amber,fontweight="bold")
    for j,name in enumerate(CASES):
        info=result["cases"][name]
        x,p,b,_,pd,bd,_ = zip(*sets[name])
        m=info["metrics"]
        a,d = ax[:,j]
        for zz in (a,d):
            zz.set_axisbelow(True)
            zz.grid(axis="y",color=grid,linewidth=.75)
            zz.set_xlim(0,x[-1])
            zz.tick_params(axis="both",labelsize=9,length=0,pad=5)
            zz.xaxis.set_major_locator(MultipleLocator(max(1,x[-1]//4)))
            for k in ("top","right","left"):
                zz.spines[k].set_visible(False)
            for w in info["stress_windows"]:
                zz.axvspan(w["first"]-.5,w["last"]+.5,color=amber,alpha=.10,linewidth=0)
        a.axhline(1,color=grid,linewidth=1.1)
        d.axhline(0,color=grid,linewidth=1.1)
        a.plot(x,p,color=navy,lw=2.1,label="Portfolio, after fees")
        a.plot(x,b,color=amber,lw=1.85,ls="--",label="Synthetic benchmark")
        d.plot(x,[100*v for v in pd],color=navy,lw=1.7)
        d.plot(x,[100*v for v in bd],color=amber,lw=1.55,ls="--")
        label="Original calibrated demo" if j==0 else "Unfitted sell-off"
        a.set_title(label,loc="left",color=ink,fontsize=13,fontweight="bold",pad=26)
        a.text(0,1.04,f"Total return: {m['portfolio_total_return']:+.2%}  vs  {m['benchmark_total_return']:+.2%}",
               transform=a.transAxes,color=muted,fontsize=9,va="bottom")
        d.set_title(f"Max drawdown: {m['portfolio_max_drawdown']:.2%}  vs  {m['benchmark_max_drawdown']:.2%}",
                    loc="left",color=ink,fontsize=10.5,pad=10)
        d.set_xlabel("Synthetic session",fontsize=9)
        a.set_ylim(min(nav)-.025,max(nav)+.028)
        d.set_ylim(min(dd)*107.5,.9)
        a.yaxis.set_major_locator(MaxNLocator(6))
        d.yaxis.set_major_locator(MaxNLocator(6))
        a.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f"{v:.2f}x"))
        d.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f"{v:g}%"))
    ax[0,0].set_ylabel("Normalized NAV",fontsize=10,labelpad=10)
    ax[1,0].set_ylabel("Drawdown from prior peak",fontsize=10,labelpad=10)
    handles, labels=ax[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="upper left",bbox_to_anchor=(.095,.886),
               ncol=2,frameon=False,labelcolor=ink,fontsize=10,borderaxespad=0)
    fig.text(.10,.055,"Shaded: pre-set sell-off shocks   |   Benchmarks modeled fee-free"
             "   |   Author: "+result["author"],fontsize=8.5,color=muted)
    stem.parent.mkdir(parents=True,exist_ok=True)
    for f in formats:
        if stem.with_suffix("."+f).exists():
            raise FileExistsError(stem.with_suffix("."+f))
    for f in formats:
        out=stem.with_suffix("."+f)
        meta={"Title":"Synthetic portfolio and benchmark comparison",
              "Description":"Two synthetic scenarios with matched axes; no market data or actual portfolio performance."}
        if f == "svg":
            fig.savefig(out,metadata={**meta,"Date":None})
        elif f == "png":
            fig.savefig(out,dpi=146,metadata=meta)
        else:
            raise ValueError("unsupported output format")
    plt.close(fig)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True,help="path stem")
    p.add_argument("--format",choices=("svg","png"),dest="formats",action="append")
    a=p.parse_args()
    render(a.run,a.output,a.formats or ("svg","png"))
