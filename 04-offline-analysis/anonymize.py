"""
Step 1: turn a confidential spreadsheet into something an AI may see.

For every column it decides what kind of data it holds and what to do with it:
  names     -> replaced by labels (Lawyer 1, Client 2 ...), the same person always
               gets the same label, so the AI still sees who did what;
  codes     -> case and contract numbers replaced by CODE-01, CODE-02 ...;
  free text -> replaced by "[text, 34 characters]", so the AI knows a text is there;
  money     -> amounts and rates changed by a random factor, keeping their format
               and rough size (hours, counts and the like are kept);
  the rest  -> kept (dates, roles, activity types and other harmless categories).

It writes 3 things:
  for_ai/sample_for_ai.xlsx   the first rows, anonymized       -> may go to the AI
  for_ai/structure.md         a plain description of the file  -> may go to the AI
  keep_private/mapping.csv    which label stands for whom      -> never leaves the computer

Nothing here uses the internet. Run alone: python anonymize.py path/to/file.xlsx
"""
import random
import re
import sys
from pathlib import Path

import pandas as pd

KINDS = {
    "name": "Names: replace with labels",
    "code": "Case or contract numbers: replace with codes",
    "text": "Free text: hide, keep only the length",
    "number": "Money: change the values, keep the format",
    "keep": "Keep as it is",
}
NAME_WORDS = ("name", "lawyer", "client", "employee", "person", "counterparty", "partner", "author", "assignee",
              "matter", "project")
MONEY_WORDS = ("amount", "rate", "sum", "price", "fee", "salary", "cost", "total", "rub", "eur", "usd")
CODE_WORDS = ("case", "contract", "matter no", "file no", "account", "invoice no", "passport")
TEXT_WORDS = ("description", "comment", "note", "details", "narrative")
CODE_PATTERN = re.compile(r"\d+[/\-]\d+|[A-Z]{2,}\s?\d+")


def guess_kind(name: str, s: pd.Series) -> str:
    """A first guess for 1 column; the person checks it in the app."""
    low = name.lower()
    if pd.api.types.is_datetime64_any_dtype(s):
        return "keep"
    if pd.api.types.is_numeric_dtype(s):
        # a running number (1, 2, 3 ...) is harmless
        if s.is_monotonic_increasing and s.is_unique:
            return "keep"
        # money is changed; hours, counts and the like are kept
        return "number" if any(w in low for w in MONEY_WORDS) else "keep"
    if any(w in low for w in TEXT_WORDS):
        return "text"
    if any(w in low for w in CODE_WORDS):
        return "code"
    if any(w in low for w in NAME_WORDS):
        return "name"
    values = s.dropna().astype(str)
    if len(values) and values.str.match(CODE_PATTERN).mean() > 0.5:
        return "code"
    if len(values) and values.str.len().mean() > 30:
        return "text"
    return "keep"


def guess_plan(df: pd.DataFrame) -> dict:
    return {c: guess_kind(c, df[c]) for c in df.columns}


def _label(column: str) -> str:
    word = column.split("(")[0].strip().split()[-1] if column.strip() else "Value"
    return word[:-1] if word.endswith("s") and len(word) > 3 else word


def anonymize(df: pd.DataFrame, plan: dict, rows: int = 25, seed: int = 1):
    """Return (anonymized sample, mapping table)."""
    rng = random.Random(seed)
    out = df.head(rows).copy()
    mapping = []
    for col, kind in plan.items():
        if kind == "keep" or col not in out:
            continue
        if kind in ("name", "code"):
            labels = {}
            for v in df[col].dropna().unique():           # whole column, so labels stay stable
                n = len(labels) + 1
                labels[v] = f"{_label(col).title()} {n}" if kind == "name" else f"CODE-{n:02d}"
                mapping.append({"Column": col, "Real value": v, "Shown to the AI as": labels[v]})
            out[col] = out[col].map(labels)
        elif kind == "text":
            out[col] = out[col].apply(lambda v: "" if pd.isna(v) or str(v) == "" else f"[text, {len(str(v))} characters]")
        elif kind == "number":
            def change(v):
                if pd.isna(v):
                    return v
                new = v * rng.uniform(0.7, 1.3)
                if float(v).is_integer():
                    return int(round(new, -2)) if abs(v) >= 1000 else int(round(new))
                return round(new, len(str(v).split(".")[1]))
            out[col] = out[col].apply(change)
    return out, pd.DataFrame(mapping)


def describe(df: pd.DataFrame, sample: pd.DataFrame, plan: dict, sheets: dict) -> str:
    """A plain description of the file, for the AI, with no real values in it."""
    lines = [f"The file has {len(df)} rows. Columns:", ""]
    lines.append("| Column | Type | What it holds | Example (anonymized) |")
    lines.append("| --- | --- | --- | --- |")
    for col in df.columns:
        s = df[col]
        if pd.api.types.is_datetime64_any_dtype(s):
            typ = f"date, {s.min():%d.%m.%Y} - {s.max():%d.%m.%Y}"
        elif pd.api.types.is_numeric_dtype(s):
            typ = "number" + (", whole" if (s.dropna() % 1 == 0).all() else ", with decimals")
        else:
            typ = f"text, {s.nunique()} different values"
        example = sample[col].dropna().astype(str).iloc[0] if sample[col].notna().any() else ""
        lines.append(f"| {col} | {typ} | {KINDS[plan.get(col, 'keep')].split(':')[0]} | {example} |")
    changed = [c for c, k in plan.items() if k == "number"]
    if changed:
        lines += ["", "In the sample the values of " + ", ".join(changed) + " are changed by a random factor, "
                  "so totals in the sample do not add up; in the real file they do."]
    for name, other in sheets.items():
        lines += ["", f"A second sheet, \"{name}\", has {len(other)} rows and the columns: "
                  + ", ".join(other.columns) + "."]
    return "\n".join(lines)


def read_workbook(path):
    sheets = pd.read_excel(path, sheet_name=None)
    first = next(iter(sheets))
    return first, sheets[first], {k: v for k, v in sheets.items() if k != first}


if __name__ == "__main__":
    src = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "sample" / "time_entries_2027-01.xlsx")
    _, df, others = read_workbook(src)
    plan = guess_plan(df)
    sample, mapping = anonymize(df, plan)
    base = Path(__file__).parent
    (base / "for_ai").mkdir(exist_ok=True)
    (base / "keep_private").mkdir(exist_ok=True)
    sample.to_excel(base / "for_ai" / "sample_for_ai.xlsx", index=False)
    (base / "for_ai" / "structure.md").write_text(describe(df, sample, plan, others), encoding="utf-8")
    mapping.to_csv(base / "keep_private" / "mapping.csv", index=False)
    for col, kind in plan.items():
        print(f"{col:<16} {KINDS[kind]}")
    print("\nDone: for_ai/ may go to the AI, keep_private/ stays on this computer.")
