"""Run the example SQL statements against a locally reproduced SQLite ledger."""
import argparse
from contextlib import closing
from pathlib import Path
import sqlite3


def queries(script):
    pending=""
    for line in script.splitlines():
        if line.lstrip().startswith("--"):
            continue
        pending+=line+"\n"
        if sqlite3.complete_statement(pending):
            yield pending.strip()
            pending=""
    if pending.strip():
        raise ValueError("incomplete SQL statement")


def run(database, script):
    uri=database.resolve(strict=True).as_uri()+"?mode=ro"
    with closing(sqlite3.connect(uri,uri=True)) as db:
        for i,query in enumerate(queries(script.read_text(encoding="utf-8")),1):
            cur=db.execute(query)
            print(f"Query {i}")
            print(" | ".join(c[0] for c in cur.description))
            for row in cur:
                print(" | ".join(str(x) for x in row))
            print()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("ledger",type=Path)
    p.add_argument("--sql",type=Path,default=Path("project/pwol-drawdown-batch/practice.sql"))
    a=p.parse_args()
    run(a.ledger,a.sql)
