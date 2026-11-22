"""Plot the fixed scenario comparisons without recomputing risk metrics."""
import argparse
import json
from math import isclose,isfinite
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter,MaxNLocator,MultipleLocator

CASES=("cliff","grind","v_rebound")


def load_guard(folder):
    s=json.loads((folder/"summary.json").read_bytes())
    d=json.loads((folder/"series.json").read_bytes())
    if (s["scope"]!="SYNTHETIC_ONLY_NO_TRADE" or s["scope"]!=d["scope"] or
            s["performance_calibration"] is not False or s["market_data"] is not False):
        raise ValueError("chart accepts only the unfitted synthetic package")
    if d["columns"]!=["session","original_nav","guarded_nav","benchmark_nav","original_drawdown",
                       "guarded_drawdown","benchmark_drawdown","guarded_target_exposure"]:
        raise ValueError("wrong series schema")
    for k in CASES:
        rows=d["cases"][k]
        if (len(rows)!=s["cases"][k]["metrics"]["guarded"]["sessions"]+1 or
                not all(len(row)==8 and row[0]==i and all(isfinite(x) for x in row)
                        and 0<row[-1]<=1 for i,row in enumerate(rows))):
            raise ValueError("bad path data")
        for i,key in enumerate(("original","guarded","benchmark"),1):
            m=s["cases"][k]["metrics"][key]
            if (not isclose(rows[-1][i]-1,m["total_return"],abs_tol=1e-10) or
                    not isclose(min(r[i+3] for r in rows),m["max_drawdown"],abs_tol=1e-10)):
                raise ValueError("NAV or drawdown mismatch")
    return s,d["cases"]


def render(folder,stem,formats=("svg","png")):
    s,d=load_guard(folder)
    nav=[x for r in d.values() for a in r for x in a[1:4]]
    dd=[100*x for r in d.values() for a in r for x in a[4:7]]
    ink,muted,grid="#13283a","#49616f","#dce7ee"
    original,guarded,bmk="#526672","#006a85","#a24b1b"
    plt.rcParams.update({"font.family":"DejaVu Sans","axes.facecolor":"white","axes.edgecolor":grid,
                         "axes.labelcolor":ink,"xtick.color":muted,"ytick.color":muted,
                         "svg.hashsalt":"pdrawer-drawdown-guard-v1","svg.fonttype":"none"})
    fig, ax=plt.subplots(3,3,figsize=(13.9,7.8),sharex="col",sharey="row",facecolor="white",
                         gridspec_kw={"height_ratios":[2.7,2.7,.85]})
    fig.subplots_adjust(left=.096,right=.975,bottom=.13,top=.756,wspace=.13,hspace=.52)
    fig.text(.096,.949,"Drawdown guard: protection vs. missed rebound",fontsize=22,fontweight="bold",color=ink)
    fig.text(.096,.912,"SYNTHETIC PATHS ONLY  /  NOT ACTUAL PWOL PERFORMANCE",fontsize=10,
             fontweight="bold",color=bmk)
    for j,k in enumerate(CASES):
        q=s["cases"][k]
        x,n,g,b,nd,gd,bd,exp=zip(*d[k])
        top,risk,mode=ax[:,j]
        for a in (top,risk,mode):
            a.set_xlim(0,x[-1]);a.set_axisbelow(True)
            a.grid(axis="y",color=grid,linewidth=.75)
            a.tick_params(axis="both",length=0,labelsize=8.5,pad=4)
            a.xaxis.set_major_locator(MultipleLocator(x[-1]//4))
            for z in ("top","right","left"):
                a.spines[z].set_visible(False)
            lo,hi=q["selloff"]
            a.axvspan(lo-.5,hi+.5,color=bmk,alpha=.09,linewidth=0)
        for a,values,scale in ((top,(n,g,b),1),(risk,(nd,gd,bd),100)):
            for values_,color,style,name in zip(values,(original,guarded,bmk),("-", "-", "--"),
                                               ("Original","Drawdown guard","Shared synthetic benchmark")):
                a.plot(x,[v*scale for v in values_],color=color,ls=style,lw=2 if color==guarded else 1.45,
                       alpha=1 if color!=original else .86,label=name)
        top.axhline(1,color=grid,linewidth=1)
        risk.axhline(0,color=grid,linewidth=1)
        top.set_ylim(min(nav)-.024,max(nav)+.034)
        risk.set_ylim(min(dd)*1.13,1.)
        top.yaxis.set_major_locator(MaxNLocator(5))
        risk.yaxis.set_major_locator(MaxNLocator(5))
        top.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f"{v:.2f}x"))
        risk.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f"{v:g}%"))
        top.set_title(q["label"],loc="left",fontsize=12,fontweight="bold",color=ink,pad=29)
        top.text(0,1.055,f"Net return: {q['metrics']['original']['total_return']:+.1%} to "
                  f"{q['metrics']['guarded']['total_return']:+.1%}",
                  transform=top.transAxes,fontsize=9,color=muted,va="bottom")
        risk.set_title(f"Drawdown saved: {q['drawdown_reduction_pp']:+.2f} pp",
                       loc="left",fontsize=9.7,color=ink,pad=9)
        mode.set_title(f"Rebound gap: {q['rebound_foregone_pp']:+.2f} pp",
                       loc="left",fontsize=9.2,color=ink,pad=7)
        mode.step(x,[100*v for v in exp],where="post",lw=1.75,color=guarded)
        mode.set_ylim(40,108);mode.set_yticks([50,100],["50%","100%"])
        mode.set_xlabel("Synthetic session",fontsize=8.5)
    ax[0,0].set_ylabel("Net NAV",fontsize=10)
    ax[1,0].set_ylabel("Drawdown",fontsize=10)
    ax[2,0].set_ylabel("Exposure",fontsize=8.5)
    h,l=ax[0,0].get_legend_handles_labels()
    fig.legend(h,l,loc="upper left",bbox_to_anchor=(.092,.892),
               ncol=3,frameon=False,labelcolor=ink,fontsize=9.8,borderaxespad=0)
    fig.text(.096,.053,"Shaded = prescribed sell-off   |   Rebound gap = original minus guarded window return"
             "   |   Mode uses prior-close NAV",color=muted,fontsize=8.5)
    stem.parent.mkdir(parents=True,exist_ok=True)
    for f in formats:
        if stem.with_suffix("."+f).exists():
            raise FileExistsError(stem.with_suffix("."+f))
    for f in formats:
        m={"Title":"Synthetic drawdown guard stress comparison",
           "Description":"Three synthetic scenarios. Common axes for wealth, drawdown and target exposure. Not actual PWOL performance."}
        if f=="svg":
            fig.savefig(stem.with_suffix(".svg"),metadata={**m,"Date":None})
        elif f=="png":
            fig.savefig(stem.with_suffix(".png"),dpi=145,metadata=m)
        else:
            raise ValueError("unsupported export format")
    plt.close(fig)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--format",choices=("svg","png"),dest="formats",action="append")
    a=p.parse_args()
    render(a.run,a.output,a.formats or ("svg","png"))
