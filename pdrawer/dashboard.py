"""Draw a portfolio dashboard from results without changing its metrics."""
import argparse
import json
from math import isfinite, prod
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator, MultipleLocator


def load_artifacts(folder):
    summary = json.loads((folder/"summary.json").read_text(encoding="utf-8"))
    series = json.loads((folder/"series.json").read_text(encoding="utf-8"))
    cols = ["session","nav","daily_net_return","drawdown","gross_turnover","fees"]
    if series["columns"] != cols or summary["scope"] != series["scope"]:
        raise ValueError("scope or schema mismatch")
    rows = series["rows"]
    m = summary["metrics"]
    if len(rows) != m["sessions"] + 1 or any(
            len(row) != len(cols) or row[0] != i or not all(isfinite(x) for x in row)
            for i,row in enumerate(rows)):
        raise ValueError("invalid session series")
    if (abs(rows[0][1] - m["initial_nav"]) > 1e-6 or
            abs(rows[-1][1] - m["ending_nav"]) > 1e-6 or
            abs(min(r[3] for r in rows) - m["max_drawdown"]) > 1e-10):
        raise ValueError("NAV or drawdown summary does not match series")
    return summary, list(map(list, zip(*rows)))


def render(folder, output, formats=("svg", "png")):
    summary, (ts, nav, returns, dd, tur, fee) = load_artifacts(folder)
    m = summary["metrics"]
    synthetic = summary["scope"] == "CALIBRATED_SYNTHETIC_DEMO_ONLY"
    title = "PWOL-style portfolio demo" if synthetic else summary["title"]
    bg, ink, muted, light = "#ffffff", "#142b40", "#486072", "#e2eaf0"
    brand, risk, neg = "#135c85", "#a04418", "#a13936"
    plt.rcParams.update({"font.family":"DejaVu Sans","axes.facecolor":bg,
                         "axes.edgecolor":light,"axes.labelcolor":ink,
                         "xtick.color":muted,"ytick.color":muted,
                         "axes.titlesize":12,"axes.titleweight":"bold",
                         "svg.fonttype":"none","svg.hashsalt":"pdrawer-port-v1"})
    fig, axs = plt.subplots(2,2,figsize=(11.3,7.3),facecolor=bg)
    fig.subplots_adjust(left=.09,right=.965,bottom=.11,top=.69,wspace=.30,hspace=.66)
    fig.text(.09,.946,title,fontsize=22,fontweight="bold",color=ink,va="center")
    scope = ("CALIBRATED SYNTHETIC DATA  /  NOT ACTUAL PWOL PERFORMANCE"
             if synthetic else summary["scope"])
    fig.text(.09,.904,scope,fontsize=10,color=risk,fontweight="bold")
    hdr = [
        ("Net total return",f"{m['total_return']:.2%}"),
        ("Annualized Sharpe",f"{m['sharpe']:.2f}" if m["sharpe"] is not None else "n/a"),
        ("Maximum drawdown",f"{m['max_drawdown']:.2%}"),
        ("Gross turnover ex. entry",f"{m['gross_turnover_excluding_open']:.1%}")]
    for x,(label,value) in zip((.09,.318,.552,.782),hdr):
        fig.text(x,.835,value,fontsize=21,color=ink,fontweight="bold")
        fig.text(x,.807,label,fontsize=9,color=muted)
    fig.text(.09,.763,
             f"{m['sessions']} sessions  /  every {summary['rebalance_every_sessions']} sessions  /"
             f"  {summary['cost_bps']:g} bp per traded notional  /  risk-free {m['risk_free_annual']:.0%}",
             fontsize=9,color=muted)

    ax0,ax1,ax2,ax3=axs.flat
    for ax in axs.flat:
        ax.set_axisbelow(True)
        ax.yaxis.grid(True,color=light,linewidth=.8)
        ax.tick_params(axis="both",labelsize=8,length=0,pad=5)
        for s in ("top","right","left"):
            ax.spines[s].set_visible(False)
    ratio=[v/nav[0] for v in nav]
    ax0.plot(ts,ratio,color=brand,linewidth=2.1)
    ax0.axhline(1,color=muted,linestyle="--",linewidth=.8)
    ax0.yaxis.set_major_formatter(FuncFormatter(lambda x,_: f"{x:.2f}x"))
    ax0.set_title("Net NAV",loc="left",color=ink,pad=8)
    ax0.set_xlabel("Synthetic session",fontsize=8)

    depth=[x*100 for x in dd]
    ax1.fill_between(ts,depth,0,color=neg,alpha=.14)
    ax1.plot(ts,depth,color=neg,linewidth=1.35)
    bottom = min(depth)
    if bottom < 0:
        at=depth.index(bottom)
        ax1.scatter(ts[at],bottom,color=neg,s=19,zorder=4)
        ax1.set_ylim(bottom*1.23,.09)
    ax1.set_title("Drawdown from prior peak",loc="left",color=ink,pad=8)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x,_: f"{x:g}%"))
    ax1.set_xlabel("Synthetic session",fontsize=8)
    for aa in (ax0,ax1):
        aa.set_xlim(0,ts[-1])
        aa.xaxis.set_major_locator(MultipleLocator(max(1,ts[-1]//4)))
        aa.yaxis.set_major_locator(MaxNLocator(5))

    step=summary["rebalance_every_sessions"]
    chunks=[returns[i:i+step] for i in range(1,len(returns),step)]
    block_net=[100*(prod(1+x for x in b)-1) for b in chunks]
    block_tr=[100*sum(tur[i:i+step]) for i in range(1,len(tur),step)]
    blocks=list(range(1,len(chunks)+1))
    ax2.bar(blocks,block_net,width=.64,color=[brand if r>=0 else neg for r in block_net])
    ax2.axhline(0,color=muted,linewidth=.8)
    ax2.set_title("Net return by rebalance block",loc="left",color=ink,pad=8)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x,_: f"{x:g}%"))
    ax3.bar(blocks,block_tr,width=.64,color=[light]+[risk]*(len(blocks)-1))
    ax3.set_title("Gross turnover by block",loc="left",color=ink,pad=8)
    ax3.yaxis.set_major_formatter(FuncFormatter(lambda x,_: f"{x:g}%"))
    for aa in (ax2,ax3):
        aa.set_xlabel(f"Block ({step} sessions)",fontsize=8)
        aa.set_xticks(blocks)
        aa.yaxis.set_major_locator(MaxNLocator(5))
    if tur[1]>0:
        ax3.text(1,block_tr[0], "Initial",ha="left",va="bottom",fontsize=8,color=muted,clip_on=False)
    fig.text(.09,.036,"Author: "+summary["author"]+"   |   "+summary["timestamp"]+
             "   |   NAV and metrics include the modeled fee",
             color=muted,fontsize=8)
    output.parent.mkdir(parents=True,exist_ok=True)
    for f in formats:
        path=output.with_suffix("."+f)
        if path.exists():
            raise FileExistsError(path)
    for f in formats:
        if f == "svg":
            fig.savefig(output.with_suffix(".svg"),metadata={"Date":None,"Title":title,"Description":scope})
        elif f == "png":
            fig.savefig(output.with_suffix(".png"),dpi=144,facecolor=bg,
                        metadata={"Title":title,"Description":scope})
        else:
            raise ValueError("unsupported figure format")
    plt.close(fig)


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path,help="path stem, writes .svg and .png")
    p.add_argument("--format",choices=("svg","png"),action="append",dest="formats")
    args=p.parse_args()
    render(args.run,args.output,args.formats or ("svg","png"))
