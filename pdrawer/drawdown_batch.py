"""Show 64-path gate counts, paired outcomes and one prespecified example."""
import argparse
import json
from pathlib import Path


def render(run, output, formats=("svg","png")):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter

    summary,paths,example=(json.loads((run/(f+".json")).read_bytes())
                           for f in ("summary","paths","example"))
    if any(x["scope"]!="SYNTHETIC_ONLY_NO_TRADE" for x in (summary,paths,example)):
        raise ValueError("this chart only accepts the synthetic output")
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,
                         "svg.hashsalt":"pwol-drawdown-batch-v1",
                         "axes.spines.top":False,"axes.spines.right":False})
    groups=summary["cohorts"]["primary"]
    family=("fast_v","gap_chain","fake_cycles","combined")
    names=("Fast V","Gap chain","False rallies","Combined")
    palette=("#315c9e","#b74721","#6d45a0","#00796e")
    marks=("o","^","s","D")
    fig,axes=plt.subplots(2,2,figsize=(13.8,9))
    fig.subplots_adjust(left=.085,right=.968,bottom=.10,top=.825,hspace=.46,wspace=.27)
    ink="#172335"
    fig.text(.085,.941,"Drawdown control: does the rebound survive full-period costs?",
             fontsize=20,weight="bold",color=ink)
    fig.text(.085,.905,"64 pre-frozen synthetic paths   |   primary costs: 5 bp commission + 6 bp base slippage + gap surcharge",
             fontsize=10,color="#49596a")
    for ax in axes.ravel():
        ax.set_axisbelow(True)
        ax.grid(axis="y",color="#e1e7ed",lw=.7)

    top,scatter=axes[0]
    for j,k in enumerate((*family,"all")):
        count=groups[k]["gate_counts"]
        n=groups[k]["n"]
        for i,(key,color,label) in enumerate((("short_joint","#a8bbc9","Drawdown + rebound"),
                                              ("joint","#00796e","+ full-period net gate"))):
            at=j+(i-.5)*.33
            y=100*count[key]/n
            top.bar(at,y,width=.30,color=color,label=label if j==0 else None)
            top.text(at,y+1.7,f"{count[key]}/{n}",ha="center",va="bottom",fontsize=8,color=ink)
    top.set_title("A  /  How many paths pass?",loc="left",weight="bold",color=ink,pad=13)
    top.set_xticks(range(5),[*names,"All"])
    top.set_ylim(0,112)
    top.set_ylabel("Passing paths")
    top.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f"{v:g}%"))
    top.legend(frameon=False,loc="upper right",fontsize=8)

    for x in (0,):
        scatter.axvline(x,color="#8c9aad",lw=.9)
        scatter.axhline(x,color="#8c9aad",lw=.9)
    for k,name,c,m in zip(family,names,palette,marks):
        g=[r["profiles"]["primary"]["gate"] for r in paths["paths"] if r["family"]==k]
        scatter.scatter([x["tiered_minus_binary_rebound_pp"] for x in g],
                        [x["tiered_minus_binary_full_pp"] for x in g],s=31,
                        marker=m,c=c,label=name,alpha=.77,edgecolors="white",linewidths=.35)
    scatter.set_title("B  /  Tiered minus halve, each path",loc="left",weight="bold",color=ink,pad=13)
    scatter.set_xlabel("Net rebound difference (pp)")
    scatter.set_ylabel("Net full-period difference (pp)")
    scatter.legend(frameon=False,loc="best",fontsize=7.5,ncol=2)

    nav,exp=axes[1]
    x=list(range(len(example["nav"]["tiered"])))
    for ax in (nav,exp):
        for lo,hi,shock in example["design"]["intraday_shifts"]:
            if shock<0:
                ax.axvspan(lo-.5,hi+.5,color="#c67b65",lw=0,alpha=.12)
        for gap in example["design"]["overnight_gaps"]:
            ax.axvline(int(gap),color="#777485",ls=":",lw=.85)
        ax.set_xlim(x[0],x[-1])
        ax.set_xlabel("Synthetic session")
    for k,label,color,ls in (("original","Original","#315c9e","-"),
                              ("binary","8% / halve","#b74721","--"),
                              ("tiered","Tiered","#00796e","-"),
                              ("benchmark","Benchmark","#818896",":")):
        nav.plot(x,example["nav"][k],color=color,ls=ls,lw=1.5,label=label)
        if k in example["exposure"]:
            exp.step(x,[v*100 for v in example["exposure"][k]],where="post",
                     color=color,ls=ls,lw=1.5,label=label)
    nav.set_title("C  /  First combined seed: net NAV",loc="left",weight="bold",color=ink,pad=13)
    nav.set_ylabel("Wealth (start = 1)")
    nav.legend(frameon=False,ncol=2,fontsize=8)
    exp.set_title("D  /  Same seed: opening target exposure",loc="left",weight="bold",color=ink,pad=13)
    exp.set_ylabel("Target exposure")
    exp.set_yticks([25,50,75,100])
    exp.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f"{v:g}%"))
    exp.set_ylim(19,108)
    exp.legend(frameon=False,fontsize=8)
    fig.text(.085,.033,f"Shading = sell-offs   |   Vertical dotted lines = overnight gaps   |   Example fixed by order: {example['path_id']}   |   Not live performance",
             fontsize=8.5,color="#49596a")
    output.parent.mkdir(parents=True,exist_ok=True)
    out=[output.with_suffix("."+f) for f in formats]
    if any(p.exists() for p in out):
        raise FileExistsError("choose an unused plot output prefix")
    metadata={"Title":"Drawdown policy under a 64-path synthetic stress batch",
              "Description":"Short and full joint gates, paired returns, and one prespecified synthetic example."}
    for path in out:
        if path.suffix==".svg":
            with path.open("x",encoding="utf-8",newline="\n") as f:
                fig.savefig(f,format="svg",metadata={**metadata,"Date":None})
        elif path.suffix==".png":
            fig.savefig(path,dpi=155,metadata=metadata)
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
