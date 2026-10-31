"""
Check the month before billing: a small program which reads a month of time
entries from an Excel file and lists what has to be looked at before the
report goes to the client.

It works entirely on this computer:
  - it switches off its own access to the network in its first lines (below);
  - it uses only what comes with Python itself: nothing is downloaded or installed;
  - no AI and no online service is involved at any point;
  - it only reads the file you choose and never changes it; the report is a new file.

Start: double-click this file (Windows), or run  python3 check_month.pyw  (Mac).
"""

# --- 1. No network, from the first line on ---------------------------------------
# Whatever the rest of the code does, it cannot open a connection: the steps which
# every network connection in Python goes through are replaced by ones which refuse.
import socket


def _no_network(*args, **kwargs):
    raise OSError("This program does not use the network.")


socket.socket.connect = _no_network
socket.socket.connect_ex = _no_network
socket.socket.sendto = _no_network
socket.create_connection = _no_network

# --- 2. Only Python's own modules ----------------------------------------------------
import os
import re
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET

# --- 3. Settings: the column names and the limits -----------------------------------
ENTRIES_SHEET = "Time entries"
MATTERS_SHEET = "Matters"
COL = {
    "entry": "Entry", "date": "Date", "lawyer": "Lawyer", "matter": "Matter",
    "description": "Description", "hours": "Hours", "rate": "Rate (RUB/h)", "amount": "Amount (RUB)",
    "cap": "Monthly cap (hours)",
}
MAX_HOURS_A_DAY = 10
HERE = Path(__file__).resolve().parent
SAMPLE = HERE / "sample" / "time_entries_2027-01.xlsx"


# --- 4. Reading an .xlsx file with Python's own zip and XML tools --------------------
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "pr": "http://schemas.openxmlformats.org/package/2006/relationships"}


def _col_index(ref):
    letters = re.match(r"[A-Z]+", ref).group()
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_xlsx(path):
    """Return {sheet name: list of rows}, each row a list of cell values."""
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))
        rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        sheets = {}
        for s in ET.fromstring(z.read("xl/workbook.xml")).find("m:sheets", NS):
            target = rels[s.get(f"{{{NS['r']}}}id")].lstrip("/")
            target = target if target.startswith("xl/") else "xl/" + target
            rows = []
            for row in ET.fromstring(z.read(target)).iter(f"{{{NS['m']}}}row"):
                values = {}
                for c in row.findall("m:c", NS):
                    kind, v = c.get("t"), c.find("m:v", NS)
                    if kind == "s":
                        val = shared[int(v.text)]
                    elif kind == "inlineStr":
                        val = "".join(t.text or "" for t in c.iter(f"{{{NS['m']}}}t"))
                    elif v is None:
                        val = None
                    elif kind in ("str", "e"):
                        val = v.text
                    elif kind == "b":
                        val = v.text == "1"
                    else:
                        num = float(v.text)
                        val = int(num) if num.is_integer() else num
                    values[_col_index(c.get("r"))] = val
                if values:
                    rows.append([values.get(i) for i in range(max(values) + 1)])
            sheets[s.get("name")] = rows
    return sheets


def as_date(v):
    if isinstance(v, (int, float)):
        return date(1899, 12, 30) + timedelta(days=int(v))      # how Excel counts days
    if isinstance(v, str):
        for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(v.strip(), fmt).date()
            except ValueError:
                pass
    return v


def records(rows):
    head = [str(h).strip() if h is not None else "" for h in rows[0]]
    return [dict(zip(head, r + [None] * (len(head) - len(r)))) for r in rows[1:] if any(x not in (None, "") for x in r)]


# --- 5. The checks -------------------------------------------------------------------
def check(entries, matters):
    missing = [v for k, v in COL.items() if k != "cap" and v not in entries[0]]
    if missing:
        raise ValueError("These columns are not in the file: " + ", ".join(missing))
    for e in entries:
        e[COL["date"]] = as_date(e[COL["date"]])
        e[COL["hours"]] = float(e[COL["hours"]] or 0)
        e[COL["description"]] = str(e[COL["description"]] or "").strip()
    found = []

    def add(check_name, e, what_to_do):
        found.append([check_name, e.get(COL["entry"]), e[COL["date"]], e[COL["lawyer"]], e[COL["matter"]],
                      e[COL["hours"]], what_to_do])

    day = defaultdict(float)
    for e in entries:
        day[(e[COL["lawyer"]], e[COL["date"]])] += e[COL["hours"]]
    for (lawyer, d), h in sorted(day.items(), key=lambda x: x[0][1]):
        if h > MAX_HOURS_A_DAY:
            found.append([f"Day over {MAX_HOURS_A_DAY} hours", "", d, lawyer, "(all)", round(h, 2),
                          f"{h:g} hours in 1 day: confirm with the lawyer"])
    for e in entries:
        if isinstance(e[COL["date"]], date) and e[COL["date"]].weekday() >= 5:
            add("Weekend entry", e, f"{e[COL['date']]:%A}: confirm it was worked")
    seen = set()
    for e in entries:
        key = tuple(v for k, v in e.items() if k != COL["entry"])
        if key in seen:
            add("Exact duplicate", e, "Same lawyer, day, matter, hours and text as an earlier entry")
        seen.add(key)
    for e in entries:
        if not e[COL["description"]]:
            add("No description", e, "The client sees no text: ask the lawyer")
    usual = {}
    for lawyer in {e[COL["lawyer"]] for e in entries}:
        usual[lawyer] = Counter(e[COL["rate"]] for e in entries if e[COL["lawyer"]] == lawyer).most_common(1)[0][0]
    for e in entries:
        if e[COL["rate"]] != usual[e[COL["lawyer"]]]:
            add("Rate differs", e, f"{e[COL['rate']]:,.0f} instead of the usual {usual[e[COL['lawyer']]]:,.0f}")
    for e in entries:
        if abs(e[COL["hours"]] * 10 - round(e[COL["hours"]] * 10)) > 1e-6:
            add("Hours not in tenths", e, f"{e[COL['hours']]} hours: round to 0.1")
    for e in entries:
        if round(e[COL["hours"]] * float(e[COL["rate"]] or 0)) != round(float(e[COL["amount"]] or 0)):
            add("Amount does not match", e, "Hours x rate gives another amount")

    by_matter = defaultdict(lambda: [0.0, 0.0, 0])
    for e in entries:
        m = by_matter[e[COL["matter"]]]
        m[0] += e[COL["hours"]]; m[1] += float(e[COL["amount"]] or 0); m[2] += 1
    caps = {m[COL["matter"]]: m.get(COL["cap"]) for m in matters} if matters else {}
    matter_rows = []
    for name, (h, amount, n) in sorted(by_matter.items()):
        cap = caps.get(name)
        left = round(cap - h, 2) if isinstance(cap, (int, float)) else ""
        matter_rows.append([name, round(h, 2), round(amount), n, cap if cap is not None else "", left])
        if left != "" and left < 0:
            found.append(["Over the monthly cap", "", "", "(all)", name, round(h, 2),
                          f"{h:g} hours against a cap of {cap:g}: agree with the partner before billing"])
    by_lawyer = defaultdict(lambda: [0.0, 0.0, set()])
    for e in entries:
        x = by_lawyer[e[COL["lawyer"]]]
        x[0] += e[COL["hours"]]; x[1] += float(e[COL["amount"]] or 0); x[2].add(e[COL["date"]])
    lawyer_rows = sorted(([k, round(h, 2), round(a), len(d)] for k, (h, a, d) in by_lawyer.items()),
                         key=lambda r: -r[1])
    dates = [e[COL["date"]] for e in entries if isinstance(e[COL["date"]], date)]
    summary = [
        ["Month", f"{min(dates):%B %Y}" if dates else ""],
        ["Entries", len(entries)],
        ["Hours", round(sum(e[COL["hours"]] for e in entries), 2)],
        ["Amount (RUB)", round(sum(float(e[COL["amount"]] or 0) for e in entries))],
        ["Matters", len(by_matter)],
        ["Entries to check", len(found)],
    ]
    return summary, found, matter_rows, lawyer_rows


# --- 6. Writing the report as an .xlsx file, again with Python's own tools ----------
def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _cell(ref, v, bold=False):
    s = ' s="1"' if bold else ""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return f'<c r="{ref}"{s}><v>{v}</v></c>'
    if isinstance(v, date):
        v = f"{v:%d.%m.%Y}"
    return f'<c r="{ref}"{s} t="inlineStr"><is><t>{escape(str(v if v is not None else ""))}</t></is></c>'


def _letter(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def write_xlsx(path, sheets):
    """sheets: list of (name, header, rows)."""
    def sheet_xml(header, rows):
        all_rows = [header] + rows
        widths = [min(70, max(len(str(r[i])) if i < len(r) and r[i] is not None else 0 for r in all_rows) + 3)
                  for i in range(len(header))]
        cols = "".join(f'<col min="{i+1}" max="{i+1}" width="{w}" customWidth="1"/>' for i, w in enumerate(widths))
        body = []
        for n, r in enumerate(all_rows, 1):
            cells = "".join(_cell(f"{_letter(i)}{n}", v, bold=(n == 1)) for i, v in enumerate(r))
            body.append(f'<row r="{n}">{cells}</row>')
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<worksheet xmlns="{NS["m"]}"><cols>{cols}</cols><sheetData>{"".join(body)}</sheetData></worksheet>')

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                   + "".join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                             for i in range(1, len(sheets) + 1)) + "</Types>")
        z.writestr("_rels/.rels",
                   f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="{NS["pr"]}">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml",
                   f'<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="{NS["m"]}" xmlns:r="{NS["r"]}"><sheets>'
                   + "".join(f'<sheet name="{escape(n)}" sheetId="{i}" r:id="rId{i}"/>' for i, (n, _, _) in enumerate(sheets, 1))
                   + "</sheets></workbook>")
        z.writestr("xl/_rels/workbook.xml.rels",
                   f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="{NS["pr"]}">'
                   + "".join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
                             for i in range(1, len(sheets) + 1))
                   + f'<Relationship Id="rId{len(sheets) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        z.writestr("xl/styles.xml",
                   f'<?xml version="1.0" encoding="UTF-8"?><styleSheet xmlns="{NS["m"]}">'
                   '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
                   '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
                   '<borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs>'
                   '<cellXfs count="2"><xf fontId="0"/><xf fontId="1" applyFont="1"/></cellXfs>'
                   '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')
        for i, (_, header, rows) in enumerate(sheets, 1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", sheet_xml(header, rows))


CHECK_HEAD = ["Check", "Entry", "Date", "Lawyer", "Matter", "Hours", "What to do"]


def run(path):
    book = read_xlsx(path)
    entries = records(book.get(ENTRIES_SHEET) or next(iter(book.values())))
    matters = records(book[MATTERS_SHEET]) if MATTERS_SHEET in book else []
    return check(entries, matters)


def save_report(path, result):
    summary, found, matter_rows, lawyer_rows = result
    out = Path(path).with_name(f"report_{Path(path).stem}.xlsx")
    write_xlsx(out, [
        ("Summary", ["", "Value"], summary),
        ("To check", CHECK_HEAD, found),
        ("By matter", ["Matter", "Hours", "Amount (RUB)", "Entries", "Monthly cap (hours)", "Left of the cap"], matter_rows),
        ("By lawyer", ["Lawyer", "Hours", "Amount (RUB)", "Days"], lawyer_rows),
    ])
    return out


# --- 7. The window -------------------------------------------------------------------
def main():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title("Check the month before billing")
    root.geometry("1300x740")
    root.configure(bg="white")
    style = ttk.Style()
    style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
    style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
    big = ("Segoe UI", 11)
    state = {"path": None, "result": None}

    tk.Label(root, text="Check the month before billing", font=("Segoe UI", 20, "bold"), bg="white").pack(anchor="w", padx=24, pady=(18, 4))
    tk.Label(root, text="🔒  This program works without the internet: it switches off its own network access when it starts, "
                        "uses no AI and no online service, and only reads your file, never changes it.",
             font=big, bg="#e7f4e4", fg="#1d5c2a", wraplength=1240, justify="left", padx=12, pady=10).pack(fill="x", padx=24, pady=(4, 14))

    def step(n, text):
        f = tk.Frame(root, bg="white"); f.pack(fill="x", padx=24, pady=6)
        tk.Label(f, text=f" {n} ", font=("Segoe UI", 13, "bold"), bg="#1f3a5f", fg="white").pack(side="left")
        tk.Label(f, text="  " + text, font=("Segoe UI", 13, "bold"), bg="white").pack(side="left")
        return f

    f1 = step(1, "Choose the Excel file")
    file_label = tk.Label(f1, text="", font=big, bg="white", fg="#555")
    f2 = step(2, "Check it")
    summary_label = tk.Label(f2, text="", font=big, bg="white")
    tree = ttk.Treeview(root, columns=CHECK_HEAD, show="headings", height=11)
    for c, w in zip(CHECK_HEAD, (165, 55, 90, 135, 215, 55, 540)):
        tree.heading(c, text=c); tree.column(c, width=w, anchor="w")
    tree.pack(fill="both", expand=True, padx=24, pady=(4, 6))
    f3 = step(3, "Save the report")
    saved_label = tk.Label(f3, text="", font=big, bg="white", fg="#555")

    def choose(path=None):
        path = path or filedialog.askopenfilename(title="Choose the Excel file", filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        state["path"], state["result"] = path, None
        file_label.config(text=f"   {Path(path).name}")
        summary_label.config(text=""); saved_label.config(text="")
        tree.delete(*tree.get_children())
        b_check.config(state="normal"); b_save.config(state="disabled")

    def do_check():
        try:
            state["result"] = run(state["path"])
        except Exception as e:  # shown in plain words, not as a crash
            messagebox.showerror("The file could not be checked", str(e))
            return
        summary, found, _, _ = state["result"]
        s = dict(summary)
        summary_label.config(text=f"   {s['Month']} · {s['Entries']} entries · {s['Hours']:g} hours · "
                                  f"{len(found)} to check before billing")
        tree.delete(*tree.get_children())
        for r in found:
            tree.insert("", "end", values=[f"{v:%d.%m.%Y}" if isinstance(v, date) else f"{v:g}" if isinstance(v, float) else v
                                           for v in r])
        b_save.config(state="normal")

    def do_save():
        out = save_report(state["path"], state["result"])
        saved_label.config(text=f"   Saved next to your file: {out.name}")
        b_open.config(state="normal")
        state["out"] = out

    def open_folder():
        folder = str(Path(state["out"]).parent)
        if sys.platform.startswith("win"):
            os.startfile(folder)
        else:
            subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", folder])

    b_choose = ttk.Button(f1, text="Choose a file…", command=choose)
    b_sample = ttk.Button(f1, text="Use the sample file", command=lambda: choose(str(SAMPLE)))
    b_check = ttk.Button(f2, text="Check the month", command=do_check, state="disabled")
    b_save = ttk.Button(f3, text="Save the report next to the file", command=do_save, state="disabled")
    b_open = ttk.Button(f3, text="Open the folder", command=open_folder, state="disabled")
    for b, f in ((b_choose, f1), (b_sample, f1), (b_check, f2), (b_save, f3), (b_open, f3)):
        b.pack(side="left", padx=(12, 0), ipady=3)
    file_label.pack(side="left"); summary_label.pack(side="left"); saved_label.pack(side="left")

    if len(sys.argv) > 1 and sys.argv[1] == "--demo":     # used only to make the screenshots
        choose(str(SAMPLE)); do_check()
    root.mainloop()


if __name__ == "__main__":
    main()
