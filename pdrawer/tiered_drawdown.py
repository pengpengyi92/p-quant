"""Draw net NAV, drawdown and opening target modes from a frozen replay."""
import argparse
import json
from pathlib import Path


def render(run, output, formats=("svg","png")):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter

    summary=json.loads((run/"summary.json").read_bytes())
    series=json.loads((run/"series.json").read_bytes())
    if summary["scope"] != "SYNTHETIC_ONLY_NO_TRADE" or series["scope"] != summary["scope"]:
        raise ValueError("this plot accepts only the synthetic fixture")
    cols={name:i for i,name in enumerate(series["columns"])}
    keys=("original","binary","tiered","benchmark")
    labels=("Original","8% / halve","Tiered","Matched benchmark")
    colors=("#185495","#ba4b28","#007f75","#797d89")
    styles=("-", "--", "-", ":")
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,
                         "svg.hashsalt":"pwol-tiered-drawdown-v1","axes.spines.top":False,
                         "axes.spines.right":False})
    ink="#162235"
    fig,axes=plt.subplots(3,3,figsize=(15,9),sharey="row",sharex=True,
                           gridspec_kw={"height_ratios":[1.1,1.1,.8]})
    fig.subplots_adjust(left=.09,right=.98,top=.81,bottom=.11,hspace=.37,wspace=.16)
    fig.text(.09,.941,"What does stepwise re-risking buy?",fontsize=24,weight="bold",color=ink)
    fig.text(.09,.906,"PWOL-style stress test  /  SYNTHETIC ONLY  /  5 bp per traded notional",
             color="#485569",fontsize=11)
    for j,key in enumerate(("new_v","gap","false")):
        case=summary["cases"][key]
        nav,dd,mode=axes[:,j]
        data=series["cases"][key]
        def read(name):
            return [v[cols[name]] for v in data]
        x=read("session")
        for ax in (nav,dd,mode):
            ax.grid(axis="y",color="#e2e7ed",linewidth=.65)
            ax.set_axisbelow(True)
            for a,b,magnitude in case["design"]["intraday_shifts"]:
                if magnitude<0:
                    ax.axvspan(a-.5,b+.5,color="#c37e69",alpha=.14,lw=0)
            for g in case["design"]["overnight_gaps"]:
                ax.axvline(int(g),color="#554059",lw=.9,ls="--",alpha=.7)
        for k,label,color,ls in zip(keys,labels,colors,styles):
            for ax,kind,factor in ((nav,"nav",1),(dd,"drawdown",100)):
                ax.plot(x,[factor*v for v in read(k+"_"+kind)],color=color,
                        ls=ls,lw=1.6 if k=="tiered" else 1.25,label=label)
        for k,color,ls in zip(keys[1:3],colors[1:3],styles[1:3]):
            mode.step(x,[100*v for v in read(k+"_exposure")],where="post",color=color,ls=ls,lw=1.55)
        mode.set_ylim(18,108)
        mode.set_yticks([25,50,75,100])
        q=case["primary"]
        nav.set_title(case["design"]["label"],loc="left",weight="bold",color=ink,pad=15)
        dd.set_title(f"Tiered vs original MDD: {q['tiered_drawdown_saved_pp']:+.2f} pp saved",
                     loc="left",fontsize=9,color=ink,pad=6)
        mode.set_title(f"Rebound: tiered vs halve {q['tiered_minus_binary_window_net_pp']:+.2f} pp",
                       loc="left",fontsize=9,color=ink,pad=6)
        mode.set_xlim(0,len(x)-1)
        mode.set_xlabel("Synthetic session")
    axes[0,0].set_ylabel("Net NAV")
    axes[0,0].yaxis.set_major_formatter(FuncFormatter(lambda v,_:f"{v:.2f}x"))
    for row,title in ((1,"Drawdown"),(2,"Target exposure")):
        axes[row,0].set_ylabel(title)
        axes[row,0].yaxis.set_major_formatter(FuncFormatter(lambda v,_:f"{v:g}%"))
    handles,legend=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,legend,ncol=4,frameon=False,loc="upper left",
               bbox_to_anchor=(.09,.884),borderaxespad=0,labelcolor=ink)
    fig.text(.09,.045,"Shading: preset sell-offs   |   Vertical dash: overnight gap   |   Exposure is a target, not an intraday position",
             color="#485569",fontsize=9)
    output.parent.mkdir(parents=True,exist_ok=True)
    paths=[output.with_suffix("."+f) for f in formats]
    if any(p.exists() for p in paths):
        raise FileExistsError("choose a new plot output prefix")
    meta={"Title":"Synthetic PWOL tiered drawdown comparison",
          "Description":"Three policy variants on three synthetic paths, against equal-weight buy-and-hold."}
    for p in paths:
        if p.suffix==".svg":
            with p.open("x",encoding="utf-8",newline="\n") as f:
                fig.savefig(f,format="svg",metadata={**meta,"Date":None})
        elif p.suffix==".png":
            fig.savefig(p,dpi=150,metadata=meta)
        else:
            raise ValueError("unsupported figure format")
    plt.close(fig)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--format",choices=("svg","png"),action="append",dest="formats")
    a=p.parse_args()
    render(a.run,a.output,a.formats or ("svg","png"))
