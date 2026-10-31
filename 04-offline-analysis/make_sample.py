"""
Make the fictional "real" file for the demo: 1 month of time entries of a law
firm for its clients, as the billing system would export it, with a few
problems planted in it on purpose (the kind a monthly report has to catch).

Everything here is invented: the firm, the lawyers, the clients, the cases.
Only for making the sample, and the only file here which needs an extra package (pandas);
the program itself, check_month.pyw, needs nothing but Python.
Run: python make_sample.py  ->  sample/time_entries_2027-01.xlsx
"""
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

random.seed(7)
OUT = Path(__file__).parent / "sample" / "time_entries_2027-01.xlsx"

LAWYERS = {  # name: (role, standard hourly rate, RUB)
    "Belova Irina": ("Partner", 32000),
    "Orlov Pavel": ("Senior associate", 22000),
    "Tikhonova Olga": ("Associate", 16000),
    "Gromov Sergei": ("Associate", 16000),
    "Lebedeva Natalia": ("Junior associate", 11000),
    "Zaitsev Dmitri": ("Paralegal", 6000),
}
MATTERS = [  # client, matter, case number, monthly cap in hours (None = no cap)
    ("Northwind Trading LLC", "Supply contract dispute", "A40-118734/2026", 140),
    ("Northwind Trading LLC", "Debt recovery, 3 debtors", "A40-201556/2026", 80),
    ("Blue Harbour Shipping JSC", "Charter party arbitration", "ICAC 77/2026", 120),
    ("Kestrel Foods LLC", "Lease termination", "A41-55210/2026", 60),
    ("Kestrel Foods LLC", "Advice on a trademark claim", "-", None),
    ("Meridian Capital Ltd", "Enforcement of a foreign award", "A40-9931/2027", 110),
]
ACTIVITIES = {
    "Drafting": ["Drafted the statement of claim", "Drafted a reply to the defence", "Revised the settlement draft",
                 "Drafted a motion to adjourn", "Prepared written explanations"],
    "Hearing": ["Attended the hearing", "Attended the preliminary hearing", "Hearing, travel included"],
    "Research": ["Researched case law on penalties", "Reviewed court practice on jurisdiction",
                 "Analysed the counterparty's documents"],
    "Client call": ["Call with the client on strategy", "Call with the client's CFO", "Meeting at the client's office"],
    "Documents": ["Prepared the evidence bundle", "Certified translations ordered", "Filed documents with the court"],
}

def workdays(year, month):
    d = date(year, month, 1)
    while d.month == month:
        if d.weekday() < 5:
            yield d
        d += timedelta(days=1)

rows = []
days = [d for d in workdays(2027, 1) if d.day >= 11]   # the first January days are holidays
for d in days:
    for lawyer, (role, rate) in LAWYERS.items():
        budget = random.choice([6, 7, 7.5, 8])
        while budget > 0.5:
            client, matter, case, cap = random.choice(MATTERS)
            activity = random.choice(list(ACTIVITIES))
            hours = min(budget, random.choice([0.5, 1, 1.5, 2, 2.5, 3]))
            budget -= hours
            rows.append({"Date": d, "Lawyer": lawyer, "Role": role, "Client": client, "Matter": matter,
                         "Case no.": case, "Activity": activity,
                         "Description": random.choice(ACTIVITIES[activity]),
                         "Hours": hours, "Rate (RUB/h)": rate})

df = pd.DataFrame(rows)

# --- problems planted on purpose -------------------------------------------
# 1. a day over 10 hours
extra = df[(df["Lawyer"] == "Orlov Pavel") & (df["Date"] == date(2027, 1, 20))].iloc[0].copy()
extra["Hours"], extra["Description"] = 4.5, "Prepared the evidence bundle"
df = pd.concat([df, extra.to_frame().T])
# 2. a weekend entry
wk = df.iloc[5].copy(); wk["Date"] = date(2027, 1, 23); df = pd.concat([df, wk.to_frame().T])
# 3. an exact duplicate
df = pd.concat([df, df.iloc[[40]]])
# 4. missing descriptions
df.iloc[[12, 77], df.columns.get_loc("Description")] = ""
# 5. a rate which differs from the lawyer's standard rate
df.iloc[[101], df.columns.get_loc("Rate (RUB/h)")] = 25000
# 6. hours not in tenths
df.iloc[[150], df.columns.get_loc("Hours")] = 1.33

df = df.sort_values(["Date", "Lawyer"]).reset_index(drop=True)
df["Hours"] = df["Hours"].astype(float)
df["Amount (RUB)"] = (df["Hours"] * df["Rate (RUB/h)"].astype(float)).round(0)
df.insert(0, "Entry", range(1, len(df) + 1))
# 7. an amount typed over by hand
df.loc[200, "Amount (RUB)"] += 10000

caps = pd.DataFrame([{"Client": c, "Matter": m, "Case no.": n, "Monthly cap (hours)": cap}
                     for c, m, n, cap in MATTERS])

OUT.parent.mkdir(exist_ok=True)
with pd.ExcelWriter(OUT, engine="openpyxl") as w:
    df.to_excel(w, sheet_name="Time entries", index=False)
    caps.to_excel(w, sheet_name="Matters", index=False)
print(f"{len(df)} entries -> {OUT}")
