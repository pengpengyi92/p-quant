"""Write a normalized synthetic ledger and check independent SQLite aggregates."""
from collections import defaultdict

from pevluation.attribution import partition_contributions


def create_ledger(db, schema, taxonomy):
    db.executescript(schema)
    db.executemany("INSERT INTO assets VALUES(?,?,?)",
                   ((a,x["sector"],x["industry"]) for a,x in sorted(taxonomy.items())))


def write_path(db, path, windows):
    db.execute("INSERT INTO paths VALUES(?,?,?,?,?,?)", tuple(path[k] for k in
               ("path_id","family","seed","input_sha256","shock_scale","clock_shift")))
    db.executemany("INSERT INTO windows VALUES(?,?,?,?)",
                   ((path["path_id"],w,*span) for w,span in windows.items()))


def write_variant(db, key, run):
    db.executemany("INSERT INTO nav VALUES(?,?,?,?,?)",
                   ((*key,t,value) for t,value in [(0,run.initial_nav),*((s.index,s.nav) for s in run.sessions)]))
    db.executemany("INSERT INTO marks VALUES(?,?,?,?,?,?,?)",
                   ((*key,i,a,m.overnight_pnl,m.gross_pnl)
                    for i,marks in enumerate(run.asset_marks,1) for a,m in marks.items()))
    db.executemany("INSERT INTO fills VALUES(?,?,?,?,?,?,?,?,?)",
                   ((*key,f.fill_session,f.asset,f.decision_session,f.signed_notional,f.fee,f.slippage)
                    for f in run.fills))


def expected_attribution(run, taxonomy, windows):
    out={}
    for w,(start,end) in windows.items():
        parts=partition_contributions(run,taxonomy,start,end,costs_by_type=True)
        factor=100/parts["opening_nav"]
        for level in ("sector","industry"):
            for bucket,p in parts[level].items():
                out[w,level,bucket]=(factor*p["gross_pnl"],factor*p["commission"],
                                     factor*p["slippage"],p["net_contribution_pp"])
    return out


def audit_ledger(db, expectations, attribution, path_families):
    """Check both computations before aggregating SQL group contributions."""
    residuals={"path":0.,"return":0.,"attribution":0.}
    tolerance=1e-8

    def compare(label, sql, python):
        diff=abs(sql-python)
        residuals[label]=max(residuals[label],diff)
        if diff>tolerance:
            raise ArithmeticError(f"independent SQL {label} check failed: {sql} vs {python}")

    def check_keyset(name, measured, expected):
        if set(measured)!=set(expected):
            raise ArithmeticError(f"{name}: ledger has missing or extra result keys")

    rows=list(db.execute("""
        SELECT p.*, n.close_nav FROM path_audit p
        JOIN nav n USING(path_id, profile, variant) WHERE n.session=0
    """))
    check_keyset("path", (tuple(x[:3]) for x in rows), expectations)
    for path,p,v,dd,turnover,commission,slippage,initial in rows:
        m=expectations[path,p,v][0]
        for x,y in zip((100*dd,100*turnover,commission,slippage),
                       (m["max_drawdown_pp"],m["turnover_pp"],
                        m["commission_bps"]*initial/10_000,m["slippage_bps"]*initial/10_000)):
            compare("path",x,y)
    wrows=list(db.execute("SELECT path_id,profile,variant,window_id,window_return FROM window_nav"))
    check_keyset("window", (tuple(x[:4]) for x in wrows),
                 ((*k,w) for k,(_,windows) in expectations.items() for w in windows))
    for path,p,v,w,val in wrows:
        compare("return",100*val,expectations[path,p,v][1][w])

    seen=set()
    groups=defaultdict(lambda:[0.,0.,0.,0.,0])
    for path,p,v,w,level,bucket,*nums in db.execute(
            "SELECT * FROM attribution_audit ORDER BY path_id,profile,variant,window_id,level,bucket"):
        key=(path,p,v,w,level,bucket)
        seen.add(key)
        for x,y in zip(nums,attribution[key]):
            compare("attribution",x,y)
        g=groups[path_families[path],p,v,w,level,bucket]
        for i,x in enumerate(nums):
            g[i]+=x
        g[4]+=1
    check_keyset("attribution",seen,attribution)
    tables=[[*key,g[4],*(round(q/g[4],10) for q in g[:4])] for key,g in sorted(groups.items())]
    return {"variants_checked":len(rows),"windows_checked":len(wrows),"buckets_checked":len(seen),
            "max_absolute_difference":residuals,"tolerance":tolerance},tables
