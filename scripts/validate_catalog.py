"""Offline consistency checks for the public p-quant catalog and toy ledger."""
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {"diagrams", "visualization", "backtesting", "analytics", "data"}
SECTIONS = {"repo", "discussion", "paper", "report", "project", "example", "template"}
MARKDOWN_LINK = re.compile(r"!?\[[^\]\n]*\]\(([^\s()]+)\)")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_entries(entries):
    ids, upstreams = set(), set()
    for row in entries:
        key = row["id"]
        require(bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", key)) and key not in ids,
                f"invalid or duplicate id: {key}")
        ids.add(key)
        parsed = urlsplit(row["upstream"])
        require(parsed.scheme == "https" and parsed.netloc in {"github.com", "gitlab.com", "docs.structurizr.com"}
                and parsed.username is None and not parsed.query and not parsed.fragment,
                f"noncanonical upstream: {key}")
        kind = row["entry_type"]
        if kind == "upstream_repository":
            require(len(parsed.path.strip("/").split("/")) == 2 and parsed.netloc != "docs.structurizr.com",
                    f"not a repository root: {key}")
        else:
            require(kind == "official_docs", f"unknown entry type: {key}")
        identity = (parsed.netloc.lower(), parsed.path.strip("/").lower())
        require(identity not in upstreams, f"duplicate upstream: {key}")
        upstreams.add(identity)
        require(row["category"] in CATEGORIES and all(row[x].strip() for x in ("name","use","check_first")),
                f"incomplete catalog entry: {key}")
        require(row["benchmark"] == "UNMEASURED" and row["source_status"] == "UPSTREAM_CHECKED",
                f"currently only upstream-reviewed entries are accepted: {key}")
    return len(ids)


def run_reference(spec, fee=None):
    """A narrow synthetic target-holding ledger, not a reusable trading engine."""
    require(spec["synthetic"] is True and spec["market_data"] is False and spec["slippage"] == 0,
            "fixture must be synthetic and have zero slippage")
    ledger = {"cash": [], "quantity": [], "equity": [], "fee_total": 0}
    cash, held, pending = spec["initial_cash"], 0, None
    per_fill = spec["fee_per_fill"] if fee is None else fee
    for i, bar in enumerate(spec["bar"]):
        require(bar["t"] == i and isinstance(bar["close"], int) and bar["close"] > 0, "invalid timeline")
        if pending is not None:
            need = pending - held
            if need:
                price = bar["open"]
                require(isinstance(price, int) and price > 0, "missing usable next-open price")
                cash -= need * price + per_fill
                require(cash >= 0, "toy ledger cannot borrow")
                held = pending
                ledger["fee_total"] += per_fill
        ledger["cash"].append(cash)
        ledger["quantity"].append(held)
        ledger["equity"].append(cash + held * bar["close"])
        # New target is only available at this close, never this open.
        pending = bar["close_target"]
    require(pending is None, "unfilled terminal target")
    return ledger


def check_links(root, path, text):
    count = 0
    for link in MARKDOWN_LINK.findall(text):
        ref = urlsplit(link)
        if ref.scheme:
            require(ref.scheme == "https" and ref.hostname is not None and ref.username is None,
                    f"insecure external reference in {path.relative_to(root)}")
            continue
        if not ref.path:
            continue
        at = (path.parent / unquote(ref.path)).resolve()
        require(at.is_relative_to(root) and at.is_file(), f"broken relative link: {path.relative_to(root)} -> {link}")
        count += 1
    return count


def validate(root=ROOT):
    root = root.resolve()
    manifest = load(root/"repo/catalog.json")
    require(manifest["schema_version"] == 1, "unexpected catalog schema")
    rows = manifest["entries"]
    count = validate_entries(rows)
    require({r["category"] for r in rows} == CATEGORIES, "missing required category")
    for section in SECTIONS:
        require((root/section/"README.md").is_file(), f"missing section: {section}")
    for category in CATEGORIES:
        page = (root/"repo"/(category+".md")).read_text(encoding="utf-8")
        for r in (r for r in rows if r["category"] == category):
            require(f']({r["upstream"]})' in page, f'uncataloged in category page: {r["id"]}')
    files = list(root.glob("*.md"))
    for section in SECTIONS | {"pbacktest", "pevluation", "pdrawer"}:
        files.extend((root/section).rglob("*.md"))
    local_links = 0
    reports = 0
    for path in files:
        body = path.read_text(encoding="utf-8")
        require(body.startswith("# "), f"missing heading: {path.relative_to(root)}")
        local_links += check_links(root, path, body)
        if path.parent == root/"report" and path.name != "README.md":
            require("作者：" in body and re.search(r"时间：\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}",body),
                    f"report metadata missing: {path.name}")
            reports += 1
    fixture = load(root/"project/synthetic-backtest-comparison/protocol.json")
    ledger = run_reference(fixture)
    require(all(fixture["expected"][k] == v for k,v in ledger.items()), "toy ledger mismatch")
    require(run_reference(fixture,2)["cash"][-1] == fixture["expected"]["final_cash_fee_2"],
            "fee sensitivity mismatch")
    return {"entries":count,"repo_roots":sum(row["entry_type"]=="upstream_repository" for row in rows),
            "categories":len(CATEGORIES),"sections":len(SECTIONS),"relative_links":local_links,
            "reports":reports,"toy_ledger":"PASS","external_benchmarks":"UNMEASURED"}


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True))
