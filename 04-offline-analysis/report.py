"""
Step 3: the monthly time report, run on the real file, on this computer.

Written by an AI (Claude, October 2026) from the anonymized sample and the
task in PROMPT.md; it never saw the real file. Checked against the fictional
sample in sample/, where the problems were planted on purpose.

What it makes from 1 month of time entries:
  - totals by matter, against the monthly cap of each matter;
  - totals by lawyer;
  - a list of checks: entries which have to be looked at before the report
    goes to the client, each with the reason.

Run alone: python report.py path/to/file.xlsx  ->  output/report.xlsx
"""
import sys
from pathlib import Path

import pandas as pd

MAX_HOURS_A_DAY = 10


def build(entries: pd.DataFrame, matters: pd.DataFrame | None = None) -> dict:
    df = entries.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["Description"] = df["Description"].fillna("").astype(str)
    checks = []

    def flag(rows, check, detail):
        for _, r in rows.iterrows():
            checks.append({"Check": check, "Entry": r.get("Entry"), "Date": r["Date"].date(),
                           "Lawyer": r["Lawyer"], "Matter": r["Matter"], "Hours": r["Hours"], "Detail": detail(r)})

    # 1. days over the limit
    day = df.groupby(["Lawyer", "Date"])["Hours"].sum()
    for (lawyer, d), h in day[day > MAX_HOURS_A_DAY].items():
        checks.append({"Check": f"Day over {MAX_HOURS_A_DAY} hours", "Entry": None, "Date": d.date(),
                       "Lawyer": lawyer, "Matter": "(all)", "Hours": h,
                       "Detail": f"{h:g} hours in 1 day: confirm with the lawyer"})
    # 2. weekends
    flag(df[df["Date"].dt.weekday >= 5], "Weekend entry", lambda r: f"{r['Date']:%A}: confirm it was worked")
    # 3. duplicates
    same = [c for c in df.columns if c not in ("Entry",)]
    flag(df[df.duplicated(same, keep="first")], "Exact duplicate", lambda r: "Same lawyer, day, matter, hours and text as an earlier entry")
    # 4. no description
    flag(df[df["Description"].str.strip() == ""], "No description", lambda r: "The client sees no text: ask the lawyer")
    # 5. rate
    usual = df.groupby("Lawyer")["Rate (RUB/h)"].agg(lambda s: s.mode().iloc[0])
    odd = df[df["Rate (RUB/h)"] != df["Lawyer"].map(usual)]
    flag(odd, "Rate differs", lambda r: f"{r['Rate (RUB/h)']:,.0f} instead of the usual {usual[r['Lawyer']]:,.0f}")
    # 6. hours not in tenths
    flag(df[(df["Hours"] * 10).round(6) % 1 != 0], "Hours not in tenths", lambda r: f"{r['Hours']} hours: round to 0.1")
    # 7. amount
    wrong = df[(df["Hours"] * df["Rate (RUB/h)"]).round(0) != df["Amount (RUB)"]]
    flag(wrong, "Amount does not match", lambda r: "Hours x rate gives another amount")

    by_matter = (df.groupby(["Client", "Matter"])
                   .agg(Hours=("Hours", "sum"), Amount=("Amount (RUB)", "sum"), Entries=("Hours", "size"))
                   .reset_index())
    if matters is not None and "Monthly cap (hours)" in matters:
        by_matter = by_matter.merge(matters[["Matter", "Monthly cap (hours)"]], on="Matter", how="left")
        by_matter["Left of the cap"] = by_matter["Monthly cap (hours)"] - by_matter["Hours"]
        for _, r in by_matter[by_matter["Left of the cap"] < 0].iterrows():
            checks.append({"Check": "Over the monthly cap", "Entry": None, "Date": None, "Lawyer": "(all)",
                           "Matter": r["Matter"], "Hours": r["Hours"],
                           "Detail": f"{r['Hours']:g} hours against a cap of {r['Monthly cap (hours)']:g}: "
                                     f"agree with the partner before billing"})
    by_lawyer = (df.groupby("Lawyer")
                   .agg(Hours=("Hours", "sum"), Amount=("Amount (RUB)", "sum"), Days=("Date", "nunique"))
                   .reset_index().sort_values("Hours", ascending=False))
    checks = pd.DataFrame(checks, columns=["Check", "Entry", "Date", "Lawyer", "Matter", "Hours", "Detail"])
    checks["Entry"] = checks["Entry"].astype("Int64")
    summary = {
        "Month": f"{df['Date'].min():%B %Y}",
        "Entries": len(df),
        "Hours": round(df["Hours"].sum(), 2),
        "Amount (RUB)": int(df["Amount (RUB)"].sum()),
        "Matters": df["Matter"].nunique(),
        "Entries to check": len(checks),
    }
    return {"summary": summary, "by_matter": by_matter, "by_lawyer": by_lawyer, "checks": checks}


def save(result: dict, path):
    if isinstance(path, Path):
        path.parent.mkdir(exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        pd.DataFrame(list(result["summary"].items()), columns=["", "Value"]).to_excel(w, sheet_name="Summary", index=False)
        result["checks"].to_excel(w, sheet_name="To check", index=False)
        result["by_matter"].to_excel(w, sheet_name="By matter", index=False)
        result["by_lawyer"].to_excel(w, sheet_name="By lawyer", index=False)
        for ws in w.sheets.values():
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = min(60, max(10, *(len(str(c.value or "")) + 2 for c in col)))


def load(path):
    sheets = pd.read_excel(path, sheet_name=None)
    entries = sheets.get("Time entries", next(iter(sheets.values())))
    return entries, sheets.get("Matters")


if __name__ == "__main__":
    src = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "sample" / "time_entries_2027-01.xlsx")
    result = build(*load(src))
    out = Path(__file__).parent / "output" / "report.xlsx"
    save(result, out)
    for k, v in result["summary"].items():
        print(f"{k:<18} {v}")
    print(result["checks"]["Check"].value_counts().to_string())
    print(f"\nSaved: {out}")
