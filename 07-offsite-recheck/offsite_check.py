"""
Offsite re-check (Tbilisi, 18-21 March 2027).

Run:  python offsite_check.py            (the folder with the input files, or sample/)
      python offsite_check.py <folder>   (any folder with the same input files)

Reads participants.xlsx, tickets/*.pdf, airline_notices/*.txt,
tickets_and_transfers.xlsx, hotel_plan.xlsx (never modified) and writes
a numbered, dated pair of reports into output/, never overwriting an earlier run:
  offsite_report_NNN_YYYY-MM-DD_HHMM.xlsx and offsite_summary_NNN_YYYY-MM-DD_HHMM.docx
The Excel report has three sheets:
  1 Table errors   - the hand-filled table checked against tickets (+ carrier notices)
  2 Corrected plan - transfers, hotel changes, lunch / dinner / museum
  3 Coordinator    - special cases that are not rebuilt automatically
"""
import difflib
import glob
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from pypdf import PdfReader

# ----------------------------------------------------------------- settings (from rules.md)
TODAY = date(2027, 3, 14)
DAY1 = date(2027, 3, 18)
DAY_BEFORE = date(2027, 3, 17)
LAST_DAY = date(2027, 3, 21)
GROUP_WINDOW = timedelta(minutes=40)
EARLY_CHECKIN_BEFORE = time(11, 0)
EXTRA_NIGHT_BEFORE = time(6, 0)
LATE_CHECKOUT_AFTER = time(15, 0)
LUNCH_BEFORE = time(14, 0)
LUNCH_GEL = 45
MTSKHETA_DEPARTURE = time(16, 0)
MUSEUM_START, MUSEUM_END = time(15, 0), time(17, 30)
MUSEUM_MIN_FLIGHT = time(20, 30)
FREE_CANCEL_SHARE = 0.10
FREE_CANCEL_UNTIL = date(2027, 3, 15)
PICKUP_LEAD = timedelta(hours=3)   # hotel pickup = earliest departure in the group - 3 h
HOME = "Moscow"
DEST = "Tbilisi"

ITEMS = [("extra", "Extra night 17.03"), ("early", "Early check-in"), ("late", "Late check-out")]


def vehicle_for(n):
    if n <= 4:
        return "Taxi"
    if n <= 16:
        return "Minibus (Sprinter)"
    return "Bus"


# ----------------------------------------------------------------- helpers
def norm(s):
    return re.sub(r"\s+", " ", str(s or "")).strip().upper()


def fmt_d(d):
    return d.strftime("%d.%m.%Y") if d else ""


def fmt_t(t):
    return t.strftime("%H:%M") if t else ""


def cell_date(v):
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    s = str(v).strip()
    for f in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(s, f).date()
        except ValueError:
            pass
    return s  # unparseable: kept as text, will show up as a difference


def cell_time(v):
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.time().replace(second=0, microsecond=0)
    if isinstance(v, time):
        return v.replace(second=0, microsecond=0)
    s = str(v).strip()
    m = re.fullmatch(r"(\d{1,2})[:.](\d{2})(?::\d{2})?", s)
    if m:
        return time(int(m.group(1)), int(m.group(2)))
    return s


def cell_price(v):
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return int(round(v))
    digits = re.sub(r"[^\d]", "", str(v))
    return int(digits) if digits else str(v)


def show(v):
    if v is None:
        return "(empty)"
    if isinstance(v, date):
        return fmt_d(v)
    if isinstance(v, time):
        return fmt_t(v)
    return str(v)


def yes(v):
    return norm(v) in ("YES", "Y", "TRUE", "1", "ДА")


def read_sheet(path):
    ws = openpyxl.load_workbook(path, data_only=True).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    head = [str(h).strip() if h is not None else "" for h in rows[0]]
    out = []
    for r in rows[1:]:
        if r is None or all(v in (None, "") for v in r):
            continue
        out.append(dict(zip(head, r)))
    return out


# ----------------------------------------------------------------- inputs
SEG_RE = re.compile(
    r"^(?P<flight>\S+ \S+)\s+(?P<frm>.+?)\s{2,}(?P<to>.+?)\s{2,}"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+(?P<dep>\d{2}:\d{2})\s+(?P<arr>\d{2}:\d{2})\s*$")


def parse_ticket(path):
    text = "\n".join(p.extract_text() or "" for p in PdfReader(path).pages)
    t = {"file": os.path.basename(path), "text": text, "segments": []}
    m = re.search(r"Passenger:\s*([A-Z\-' ]+)/([A-Z\-' ]+)", text)
    t["surname"], t["name"] = (norm(m.group(1)), norm(m.group(2))) if m else ("", "")
    m = re.search(r"Issued:\s*(\d{2}\.\d{2}\.\d{4})(.*)", text)
    t["issued"] = datetime.strptime(m.group(1), "%d.%m.%Y").date() if m else None
    t["reissued_mark"] = bool(m and "REISSU" in m.group(2).upper())
    m = re.search(r"Fare:\s*RUB\s*([\d  ]+)", text)
    t["fare"] = int(re.sub(r"\D", "", m.group(1))) if m else None
    m = re.search(r"Form of payment:\s*(.+)", text)
    t["payment"] = m.group(1).strip() if m else ""
    t["number"] = (re.search(r"Ticket number:\s*(\S+)", text) or [None, ""])[1]
    t["pnr"] = (re.search(r"Booking reference:\s*(\S+)", text) or [None, ""])[1]
    t["rail_note"] = bool(re.search(r"\brail\b", text, re.I))
    for line in text.splitlines():
        m = SEG_RE.match(line.strip())
        if not m:
            continue
        d = datetime.strptime(m["date"], "%d.%m.%Y").date()
        dep = datetime.combine(d, datetime.strptime(m["dep"], "%H:%M").time())
        arr = datetime.combine(d, datetime.strptime(m["arr"], "%H:%M").time())
        if arr < dep:
            arr += timedelta(days=1)
        t["segments"].append({"flight": norm(m["flight"]), "frm": m["frm"].strip(),
                              "to": m["to"].strip(), "dep": dep, "arr": arr,
                              "ticket_dep": dep, "ticket_arr": arr, "notice": None})
    return t


MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}


def parse_notice(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    n = {"file": os.path.basename(path)}
    m = re.search(r"flight\s+([A-Z0-9]{2}\s?\d+)\b.*?on\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", text, re.S)
    if not m:
        return None
    n["flight"] = norm(m.group(1).replace(" ", "")[:2] + " " + m.group(1).replace(" ", "")[2:])
    n["date"] = date(int(m.group(4)), MONTHS[m.group(3).lower()], int(m.group(2)))
    hm = lambda s: datetime.strptime(s, "%H:%M").time()
    m = re.search(r"Was:\s*departure\s*(\d{2}:\d{2}),\s*arrival\s*(\d{2}:\d{2})", text)
    n["was"] = (hm(m.group(1)), hm(m.group(2))) if m else None
    m = re.search(r"Now:\s*departure\s*(\d{2}:\d{2}),\s*arrival\s*(\d{2}:\d{2})", text)
    n["now"] = (hm(m.group(1)), hm(m.group(2))) if m else None
    m = re.search(r"Date:\s*(.+)", text)
    n["sent"] = m.group(1).strip() if m else ""
    return n if n["now"] else None


# ----------------------------------------------------------------- rules (shared by the plan and the console summary)
def group_by_window(items):
    """items: (datetime, flight, who). Within GROUP_WINDOW of the first in the group = one vehicle."""
    groups = []
    for it in sorted(items, key=lambda x: x[0]):
        if groups and it[0] - groups[-1][0][0] <= GROUP_WINDOW:
            groups[-1].append(it)
        else:
            groups.append([it])
    return groups


def needs_for(arr, dep):
    extra = arr.date() < DAY1 or (arr.date() == DAY1 and arr.time() < EXTRA_NIGHT_BEFORE)
    return {"extra": extra,
            "early": (not extra) and arr.date() == DAY1 and arr.time() < EARLY_CHECKIN_BEFORE,
            "late": dep.date() == LAST_DAY and dep.time() > LATE_CHECKOUT_AFTER}


def gets_lunch(arr):
    return arr < datetime.combine(DAY1, LUNCH_BEFORE)


def at_dinner(arr):
    return arr <= datetime.combine(DAY1, MTSKHETA_DEPARTURE)


def at_museum(dep):
    return dep >= datetime.combine(LAST_DAY, MUSEUM_MIN_FLIGHT)


def match_hotel_items(free, need):
    """free/need: {item: [rooms]} -> moves, adds, cancels (transfers between rooms first)."""
    moves, adds, cancels = [], [], []
    for k, nm in ITEMS:
        f, n = list(free.get(k, [])), list(need.get(k, []))
        while f and n:
            moves.append([nm, f.pop(0), n.pop(0)])
        adds += [[nm, r] for r in n]
        cancels += [[nm, r] for r in f]
    return moves, adds, cancels


def kpis(itins, room_guests, booked_by_room, frozen):
    """itins: {pid: (arr_dt, dep_dt)}. Returns the key indicators used in the console summary."""
    veh = lambda groups: (len(groups), Counter(vehicle_for(len(g)) for g in groups))
    museum = [pid for pid, (a, d) in itins.items() if at_museum(d)]
    free, need = defaultdict(list), defaultdict(list)
    for room in sorted(booked_by_room):
        guests = room_guests.get(room, [])
        if room in frozen or not guests or any(g not in itins for g in guests):
            continue
        n = needs_for(min(itins[g][0] for g in guests), max(itins[g][1] for g in guests))
        b = booked_by_room[room]
        for k, _ in ITEMS:
            if b[k] and not n[k]:
                free[k].append(room)
            elif n[k] and not b[k]:
                need[k].append(room)
    moves, adds, cancels = match_hotel_items(free, need)
    limit = int(len(booked_by_room) * FREE_CANCEL_SHARE)
    c_rooms = len({r for _, r in cancels})
    return {"arr": veh(group_by_window([(a, "", p) for p, (a, d) in itins.items()])),
            "dep": veh(group_by_window([(d, "", p) for p, (a, d) in itins.items()])),
            "dinner": sum(at_dinner(a) for a, d in itins.values()),
            "museum": (len(museum), vehicle_for(len(museum)) if museum else "-"),
            "lunch": sum(gets_lunch(a) for a, d in itins.values()),
            "moves": len(moves), "adds": len(adds), "cancels": len(cancels), "cancel_rooms": c_rooms,
            "fits": c_rooms <= limit and TODAY <= FREE_CANCEL_UNTIL, "limit": limit}


def itinerary_from_table(row, notices):
    """Fallback for a participant without a ticket: inbound/outbound from the hand-filled table.
    Carrier notices still apply (they override times for every passenger on the flight)."""
    if not row:
        return None
    fi, fo = norm(row.get("Inbound flight")), norm(row.get("Outbound flight"))
    da, ta = cell_date(row.get("Arrival date")), cell_time(row.get("Arrival time"))
    dd, td = cell_date(row.get("Departure date")), cell_time(row.get("Departure time"))
    if not (fi and fo and isinstance(da, date) and isinstance(ta, time)
            and isinstance(dd, date) and isinstance(td, time)):
        return None
    arr, dep = datetime.combine(da, ta), datetime.combine(dd, td)
    seg_in = {"flight": fi, "frm": "?", "to": DEST, "dep": None, "arr": arr,
              "ticket_dep": None, "ticket_arr": arr, "notice": None, "from_table": True}
    seg_out = {"flight": fo, "frm": DEST, "to": "?", "dep": dep, "arr": None,
               "ticket_dep": dep, "ticket_arr": None, "notice": None, "from_table": True}
    for n in notices:
        if n["flight"] == fi and n["date"] in (da, da - timedelta(days=1)):
            seg_in["arr"] = datetime.combine(da, n["now"][1])
            seg_in["notice"] = n
        if n["flight"] == fo and n["date"] == dd:
            seg_out["dep"] = datetime.combine(dd, n["now"][0])
            seg_out["notice"] = n
    return seg_in, seg_out


def next_run_number(out_dir):
    """The next report number: 1 more than the highest already in output/."""
    nums = [int(m.group(1)) for f in os.listdir(out_dir)
            for m in [re.match(r"offsite_(?:report|summary)_(\d{3})_", f)] if m]
    return max(nums, default=0) + 1


# ----------------------------------------------------------------- main logic
def run(base):
    out_dir = os.path.join(base, "output")
    os.makedirs(out_dir, exist_ok=True)
    run_no = next_run_number(out_dir)
    stamp = datetime.now()
    tag = f"{run_no:03d}_{stamp:%Y-%m-%d_%H%M}"
    run_label = f"Report No. {run_no}, generated {stamp:%d.%m.%Y %H:%M}"

    participants = read_sheet(os.path.join(base, "participants.xlsx"))
    table = read_sheet(os.path.join(base, "tickets_and_transfers.xlsx"))
    hotel = read_sheet(os.path.join(base, "hotel_plan.xlsx"))
    tickets = [parse_ticket(p) for p in sorted(glob.glob(os.path.join(base, "tickets", "*.pdf")))]
    notices = [n for n in (parse_notice(p) for p in sorted(glob.glob(os.path.join(base, "airline_notices", "*.txt")))) if n]

    errors = []      # sheet 1
    coord = []       # sheet 3

    def add_coord(pid, who, category, found, suggestion=""):
        coord.append([pid, who, category, found, suggestion])

    P = {}
    for r in participants:
        pid = str(r["ID"]).strip()
        P[pid] = {"id": pid, "surname": norm(r["Surname (passport)"]), "name": norm(r["Name (passport)"]),
                  "type": str(r["Type"]).strip(), "room": str(r["Room"] or "").strip(),
                  "companion_of": r.get("Companion of"), "ticket": None, "special": [], "tags": []}
    label = lambda p: f"{p['surname']} {p['name']}"

    # --- apply carrier notices to ticket segments
    for n in notices:
        hits = 0
        for t in tickets:
            for s in t["segments"]:
                if s["flight"] == n["flight"] and s["ticket_dep"].date() == n["date"]:
                    hits += 1
                    if n["was"] and (s["ticket_dep"].time(), s["ticket_arr"].time()) != n["was"]:
                        add_coord("", f"{t['surname']} {t['name']}", "Notice does not match ticket",
                                  f"{n['file']}: 'was' {fmt_t(n['was'][0])}-{fmt_t(n['was'][1])}, ticket "
                                  f"{fmt_t(s['ticket_dep'].time())}-{fmt_t(s['ticket_arr'].time())}",
                                  "Confirm the current time with the carrier.")
                    d = s["ticket_dep"].date()
                    s["dep"] = datetime.combine(d, n["now"][0])
                    s["arr"] = datetime.combine(d, n["now"][1])
                    if s["arr"] < s["dep"]:
                        s["arr"] += timedelta(days=1)
                    s["notice"] = n
        n["hits"] = hits

    # --- match tickets to participants
    by_key = {(p["surname"], p["name"]): p for p in P.values()}
    for t in tickets:
        p = by_key.get((t["surname"], t["name"]))
        t["name_mismatch"] = False
        if p is None:
            cands = [q for q in P.values() if q["surname"] == t["surname"] and q["ticket"] is None]
            best = max(cands, key=lambda q: difflib.SequenceMatcher(None, q["name"], t["name"]).ratio(), default=None)
            if best and difflib.SequenceMatcher(None, best["name"], t["name"]).ratio() >= 0.7:
                p, t["name_mismatch"] = best, True
        if p is None:
            errors.append(["-", f"{t['surname']} {t['name']}", "Ticket without participant",
                           "(not on the list)", f"ticket {t['number']} ({t['file']})"])
            add_coord("", f"{t['surname']} {t['name']}", "Ticket with nobody on the list",
                      f"{t['file']}, ticket {t['number']}, PNR {t['pnr']}", "Clarify who this is; not planned.")
            continue
        if p["ticket"] is not None:
            add_coord(p["id"], label(p), "Two tickets for one participant",
                      f"{p['ticket']['file']} and {t['file']}", "Only the first is used.")
            continue
        p["ticket"] = t

    # --- derive itinerary per participant
    issued_dates = [t["issued"] for t in tickets if t["issued"]]
    usual_issue = max(set(issued_dates), key=issued_dates.count) if issued_dates else None
    for p in P.values():
        t = p["ticket"]
        p["in"] = p["out"] = None
        if not t:
            p["special"].append("no ticket")
            p["unconfirmed"] = True
            row = next((r for r in table if str(r.get("ID") or "").strip() == p["id"]), None)
            built = itinerary_from_table(row, notices)
            if built:
                p["in"], p["out"] = built
                basis = (f"Planned provisionally from the table: in {p['in']['flight']} "
                         f"{fmt_d(p['in']['arr'].date())} {fmt_t(p['in']['arr'].time())}, out {p['out']['flight']} "
                         f"{fmt_d(p['out']['dep'].date())} {fmt_t(p['out']['dep'].time())} - in all transfers and "
                         f"headcounts, marked UNCONFIRMED.")
            else:
                basis = "The table has no usable flight data either: NOT planned anywhere."
            add_coord(p["id"], label(p), "No ticket (UNCONFIRMED)",
                      f"{p['type']}, room {p['room']}: no e-ticket in tickets/. {basis}",
                      "Request the ticket (запросить билет). Hotel room left as booked.")
            continue
        segs = t["segments"]
        i_in = next((i for i, s in enumerate(segs) if s["to"].startswith(DEST)), None)
        i_out = next((i for i, s in enumerate(segs) if s["frm"].startswith(DEST) and (i_in is None or i > i_in)), None)
        p["in"] = segs[i_in] if i_in is not None else None
        p["out"] = segs[i_out] if i_out is not None else None
        route = " > ".join([segs[0]["frm"]] + [s["to"] for s in segs]) if segs else "(no segments)"
        if not segs or not segs[0]["frm"].startswith(HOME) or not segs[-1]["to"].startswith(HOME):
            p["special"].append("route not Moscow-Moscow")
            add_coord(p["id"], label(p), "Route does not start/end in Moscow", f"Route: {route}", "")
        if any(s["flight"].startswith("TRAIN") for s in segs) or t["rail_note"]:
            p["special"].append("train")
            tr = ", ".join(f"{s['flight']} {s['frm']} > {s['to']} {fmt_d(s['dep'].date())} {fmt_t(s['dep'].time())}"
                           for s in segs if s["flight"].startswith("TRAIN"))
            add_coord(p["id"], label(p), "Route includes a train", f"{tr}. Route: {route}", "")
        if t["reissued_mark"] or (usual_issue and t["issued"] and t["issued"] > usual_issue):
            p["special"].append("reissued")
            add_coord(p["id"], label(p), "Ticket reissued after the table was filled in",
                      f"Issued {fmt_d(t['issued'])}{' (REISSUED)' if t['reissued_mark'] else ''}. "
                      f"Now: in {p['in']['flight'] if p['in'] else '-'}, out {p['out']['flight'] if p['out'] else '-'} "
                      f"{fmt_d(p['out']['dep'].date()) if p['out'] else ''} {fmt_t(p['out']['dep'].time()) if p['out'] else ''}", "")
        if p["in"] is None or p["out"] is None:
            p["special"].append("incomplete itinerary")
            add_coord(p["id"], label(p), "Itinerary incomplete",
                      f"No {'arrival to' if p['in'] is None else 'departure from'} Tbilisi on the ticket. Route: {route}", "")
        if t["name_mismatch"]:
            add_coord(p["id"], label(p), "Name on ticket differs from passport",
                      f"Passport: {p['surname']} {p['name']}; ticket: {t['surname']}/{t['name']} ({t['file']})",
                      "Have the carrier correct the name; boarding may be refused.")
        pay = t["payment"].lower()
        if p["type"] == "Colleague" and "card" in pay and "corporate" not in pay:
            add_coord(p["id"], label(p), "Colleague paid own ticket", f"Form of payment: {t['payment']}", "Refund?")
        if p["type"] == "Companion" and ("invoice" in pay or "corporate" in pay):
            add_coord(p["id"], label(p), "Companion ticket paid by the firm", f"Form of payment: {t['payment']}",
                      "The firm does not pay companions' flights.")

    # notices: informational item (applied automatically, but nobody recorded them in the table)
    for n in notices:
        affected = [p for p in P.values() if p["ticket"] and any(s["notice"] is n for s in p["ticket"]["segments"])]
        stale = [p for p in affected if any(r for r in table if str(r["ID"]).strip() == p["id"])]
        add_coord("", f"{len(affected)} passengers", "Carrier schedule change (applied automatically)",
                  f"{n['file']}: {n['flight']} {fmt_d(n['date'])} was {fmt_t(n['was'][0]) if n['was'] else '?'}-"
                  f"{fmt_t(n['was'][1]) if n['was'] else '?'}, now {fmt_t(n['now'][0])}-{fmt_t(n['now'][1])}. "
                  f"Not recorded in the table.",
                  "Inform the passengers: " + ", ".join(p["id"] for p in affected))

    # --- 1. table check
    seen = set()
    for r in table:
        pid = str(r.get("ID") or "").strip()
        p = P.get(pid)
        who = str(r.get("Name") or "")
        if p is None:
            errors.append([pid or "-", who, "Row not on the participant list", "(row present)", "-"])
            continue
        seen.add(pid)

        def diff(field, tab, real):
            if tab != real:
                errors.append([pid, label(p), field, show(tab), show(real)])

        diff("Name (vs passport)", norm(r.get("Name")), f"{p['surname']} {p['name']}")
        diff("Type (vs participant list)", str(r.get("Type") or "").strip(), p["type"])
        if not p["ticket"]:
            errors.append([pid, label(p), "Ticket",
                           f"in {show(r.get('Inbound flight'))} {show(cell_date(r.get('Arrival date')))} "
                           f"{show(cell_time(r.get('Arrival time')))}, out {show(r.get('Outbound flight'))} "
                           f"{show(cell_date(r.get('Departure date')))} {show(cell_time(r.get('Departure time')))}, "
                           f"price {show(cell_price(r.get('Ticket price, RUB (firm-paid)')))}",
                           "NO TICKET in tickets/ - nothing can be verified"])
            continue
        note = lambda s, which: (f" (ticket {fmt_t(s['ticket_dep' if which == 'dep' else 'ticket_arr'].time())}; "
                                 f"carrier notice {s['notice']['sent']})") if s and s["notice"] else ""
        i, o = p["in"], p["out"]
        diff("Inbound flight", norm(r.get("Inbound flight")), i["flight"] if i else None)
        diff("Arrival date", cell_date(r.get("Arrival date")), i["arr"].date() if i else None)
        a_tab, a_real = cell_time(r.get("Arrival time")), (i["arr"].time() if i else None)
        if a_tab != a_real:
            errors.append([pid, label(p), "Arrival time", show(a_tab), show(a_real) + note(i, "arr")])
        diff("Outbound flight", norm(r.get("Outbound flight")), o["flight"] if o else None)
        diff("Departure date", cell_date(r.get("Departure date")), o["dep"].date() if o else None)
        d_tab, d_real = cell_time(r.get("Departure time")), (o["dep"].time() if o else None)
        if d_tab != d_real:
            errors.append([pid, label(p), "Departure time", show(d_tab), show(d_real) + note(o, "dep")])
        price = cell_price(r.get("Ticket price, RUB (firm-paid)"))
        if p["type"] == "Colleague":
            diff("Price, RUB", price, p["ticket"]["fare"])
        elif price is not None:
            errors.append([pid, label(p), "Price, RUB", show(price), "(empty: companion pays own flight)"])
    for pid, p in P.items():
        if pid not in seen:
            errors.append([pid, label(p), "Missing row", "(no row in the table)", "participant is on the list"])

    # --- people usable for planning
    def mark(p):
        if p.get("unconfirmed"):
            return label(p) + " (UNCONFIRMED)"
        return label(p) + (" *" if p["special"] else "")
    plan_people = [p for p in P.values() if p["in"] and p["out"]]
    excluded = [p for p in P.values() if not (p["in"] and p["out"])]

    # --- 2a. transfers
    group = group_by_window
    transfers = []
    for g in group([(p["in"]["arr"], p["in"]["flight"], p) for p in plan_people]):
        flights = sorted({x[1] for x in g}, key=lambda f: min(x[0] for x in g if x[1] == f))
        transfers.append(["Arrival: airport > hotel", fmt_d(g[0][0].date()),
                          f"{fmt_t(g[0][0].time())}" + (f"-{fmt_t(g[-1][0].time())}" if g[-1][0] != g[0][0] else ""),
                          "", ", ".join(flights), vehicle_for(len(g)), len(g), ", ".join(mark(x[2]) for x in g)])
    museum = [p for p in plan_people if at_museum(p["out"]["dep"])]
    for g in group([(p["out"]["dep"], p["out"]["flight"], p) for p in plan_people]):
        flights = sorted({x[1] for x in g}, key=lambda f: min(x[0] for x in g if x[1] == f))
        pickup = g[0][0] - PICKUP_LEAD
        transfers.append(["Departure: hotel > airport", fmt_d(g[0][0].date()),
                          f"{fmt_t(g[0][0].time())}" + (f"-{fmt_t(g[-1][0].time())}" if g[-1][0] != g[0][0] else ""),
                          f"{fmt_d(pickup.date())} {fmt_t(pickup.time())}", ", ".join(flights),
                          vehicle_for(len(g)), len(g), ", ".join(mark(x[2]) for x in g)])
    if museum:
        for leg, tm in (("Museum: hotel > museum", MUSEUM_START), ("Museum: museum > hotel", MUSEUM_END)):
            transfers.append([leg, fmt_d(LAST_DAY), fmt_t(tm), "", "-", vehicle_for(len(museum)), len(museum),
                              ", ".join(mark(p) for p in museum)])

    # --- 2b. hotel
    rooms = defaultdict(list)
    for p in P.values():
        rooms[p["room"]].append(p)
    hotel_rows = []
    free, need = defaultdict(list), defaultdict(list)
    frozen_diffs = []   # (room, item, 'add'/'free')
    frozen_rooms, booked_by_room, hotel_hint = set(), {}, defaultdict(list)
    hotel_by_room = {str(h["Room"]).strip(): h for h in hotel}
    for room in sorted(set(rooms) | set(hotel_by_room)):
        h = hotel_by_room.get(room)
        guests = rooms.get(room, [])
        ids = ", ".join(g["id"] for g in guests)
        if h is None:
            add_coord(ids, room, "Room not in the hotel plan", f"Guests {ids} have room {room}, not booked.", "Book it.")
            continue
        plan_ids = {x.strip() for x in str(h.get("Guests") or "").split(",") if x.strip()}
        if plan_ids != {g["id"] for g in guests}:
            add_coord(ids, room, "Hotel plan guests differ from participant list",
                      f"Hotel plan: {', '.join(sorted(plan_ids)) or '(none)'}; list: {ids or '(none)'}", "")
        booked = {"extra": yes(h.get("Extra night 17.03")), "early": yes(h.get("Early check-in")),
                  "late": yes(h.get("Late check-out"))}
        booked_by_room[room] = booked
        known = [g for g in guests if g["in"] and g["out"]]
        needed, why = None, ""
        if known:
            arr = min(g["in"]["arr"] for g in known)
            dep = max(g["out"]["dep"] for g in known)
            needed = needs_for(arr, dep)
            why = f"arr {fmt_d(arr.date())} {fmt_t(arr.time())}, dep {fmt_d(dep.date())} {fmt_t(dep.time())}"
            if arr.date() < DAY_BEFORE:
                add_coord(ids, room, "Arrival before 17 March", why, "More than one extra night: not in the rules.")
            if dep.date() < LAST_DAY or dep.date() > LAST_DAY:
                add_coord(ids, room, "Departure not on 21 March", why, "Room dates need changing: not in the rules.")
        frozen = any(g["special"] for g in guests) or not guests or len(known) < len(guests)
        if frozen:
            frozen_rooms.add(room)
        yn = lambda d: " / ".join(("Y" if d[k] else "N") for k, _ in ITEMS) if d else "?"
        action = []
        if needed:
            for k, nm in ITEMS:
                if booked[k] and not needed[k]:
                    (frozen_diffs.append((room, k, "free")) if frozen else free[k].append(room))
                    action.append(f"{nm}: not needed")
                elif needed[k] and not booked[k]:
                    (frozen_diffs.append((room, k, "add")) if frozen else need[k].append(room))
                    action.append(f"{nm}: needed")
        status = ("NOT CHANGED - see coordinator" if frozen else ("OK" if not action else "; ".join(action)))
        if frozen and action:
            status += " (ticket says: " + "; ".join(action) + ")"
        hotel_rows.append([room, ", ".join(mark(g) for g in guests), yn(booked), yn(needed), why or "no ticket data", status])

    moves, adds, cancels = match_hotel_items(free, need)
    limit = int(len(hotel_by_room) * FREE_CANCEL_SHARE)
    cancel_rooms = sorted({r for _, r in cancels})

    # suggestions for frozen rooms (coordinator)
    for room, k, kind in frozen_diffs:
        nm = dict(ITEMS)[k]
        guests = ", ".join(f"{g['id']} {label(g)}" for g in rooms[room])
        if kind == "free":
            target = next((a for a in adds if a[0] == nm), None)
            sug = (f"Could be transferred to {target[1]} (now planned as an addition there)." if target
                   else "Would be a cancellation (counts towards the free-cancellation limit).")
            hotel_hint[room].append(f"{room} {nm.lower()} booked, not needed: "
                                    + (f"transfer to {target[1]}" if target else "cancel"))
            add_coord(", ".join(g["id"] for g in rooms[room]), room, "Hotel: special-case room not changed",
                      f"{guests}: {nm} booked but not needed by the ticket.", sug)
        else:
            src = next((c for c in cancels if c[0] == nm), None)
            sug = (f"Could take the {nm.lower()} freed in {src[1]} (transfer)." if src else "Would be an addition.")
            hotel_hint[room].append(f"{room} needs {nm.lower()}: "
                                    + (f"transfer from {src[1]}" if src else "book it (addition)"))
            add_coord(", ".join(g["id"] for g in rooms[room]), room, "Hotel: special-case room not changed",
                      f"{guests}: {nm} needed by the ticket but not booked.", sug)

    # --- 2c. meals / activities
    lunch = [p for p in plan_people if gets_lunch(p["in"]["arr"])]
    dinner_ok = [p for p in plan_people if at_dinner(p["in"]["arr"])]
    dinner_miss = [p for p in plan_people if p not in dinner_ok]

    # ----------------------------------------------------------------- write workbook
    wb = openpyxl.Workbook()
    H = Font(bold=True, color="FFFFFF")
    HF = PatternFill("solid", fgColor="305496")
    T = Font(bold=True, size=13)
    WR = Alignment(wrap_text=True, vertical="top")

    def write(ws, row, header, data, widths=None):
        for c, v in enumerate(header, 1):
            cell = ws.cell(row, c, v)
            cell.font, cell.fill, cell.alignment = H, HF, WR
        for r_i, line in enumerate(data, row + 1):
            for c, v in enumerate(line, 1):
                ws.cell(r_i, c, v).alignment = WR
        return row + len(data) + 2

    def title(ws, row, text, font=T):
        ws.cell(row, 1, text).font = font
        return row + 1

    # sheet 1
    ws = wb.active
    ws.title = "1 Table errors"
    r = title(ws, 1, f"Table check: tickets_and_transfers.xlsx vs passports and e-tickets (+ carrier notices). "
                     f"{len(errors)} differences in {len({e[0] for e in errors})} participants.")
    order = {pid: i for i, pid in enumerate(P)}
    errors.sort(key=lambda e: order.get(e[0], 999))
    ws.cell(2, 1, run_label).font = Font(italic=True, color="666666")
    write(ws, r + 1, ["ID", "Participant (passport)", "Field", "Table says", "Ticket says (source of truth)"], errors)
    for i, w in enumerate([7, 26, 26, 30, 60], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A4"

    # sheet 2
    ws = wb.create_sheet("2 Corrected plan")
    for i, w in enumerate([28, 34, 16, 18, 20, 70, 9, 90], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    r = title(ws, 1, "Corrected plan (from e-tickets + carrier notices). * = special case, see sheet 3 (provisional). "
                     "(UNCONFIRMED) = no ticket, planned from the table - request the ticket.")
    r = title(ws, r, run_label, Font(italic=True, color="666666"))
    if excluded:
        r = title(ws, r, "Not planned (no usable ticket): " + ", ".join(f"{p['id']} {label(p)}" for p in excluded),
                  Font(italic=True, color="C00000"))
    r = title(ws, r + 1, "A. Transfers")
    ws.cell(r, 1, f"Rule: within {int(GROUP_WINDOW.total_seconds() // 60)} min of the first in the group = 1 vehicle; "
                  f"1-4 taxi, 5-16 minibus, 17+ bus. Hotel pickup = first departure - {int(PICKUP_LEAD.total_seconds() // 3600)} h.")
    r = write(ws, r + 1, ["Transfer", "Date", "Flight time(s)", "Hotel pickup", "Flight(s)", "Vehicle", "People", "Names"],
              [[t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7]] for t in transfers])
    # re-order hotel columns to fit widths: keep it simple
    r = title(ws, r, "B. Hotel")
    ws.cell(r, 1, "Booked / Needed = Extra night 17.03 / Early check-in / Late check-out")
    r = write(ws, r + 1, ["Room", "Guests", "Booked", "Needed", "Basis (earliest arr / latest dep)", "Status"], hotel_rows)
    r = title(ws, r, "B1. Transfers between rooms (request to the hotel first)", Font(bold=True))
    r = write(ws, r, ["Item", "From room (no longer needed)", "To room (needed)"], moves or [["none", "", ""]])
    r = title(ws, r, "B2. Additions (after transfers)", Font(bold=True))
    r = write(ws, r, ["Item", "Room"], adds or [["none", ""]])
    r = title(ws, r, "B3. Cancellations (after transfers)", Font(bold=True))
    r = write(ws, r, ["Item", "Room"], cancels or [["none", ""]])
    fits = len(cancel_rooms) <= limit and TODAY <= FREE_CANCEL_UNTIL
    verdict = (f"Free cancellation: {len(cancels)} item(s) in {len(cancel_rooms)} room(s); limit {limit} rooms "
               f"(10% of {len(hotel_by_room)}), deadline {fmt_d(FREE_CANCEL_UNTIL)}, today {fmt_d(TODAY)}: "
               f"{'FITS' if fits else 'DOES NOT FIT'}. Special-case rooms not included - see sheet 3.")
    r = title(ws, r, verdict, Font(bold=True, color="006100" if fits else "C00000")) + 1
    r = title(ws, r, "C. Meals and activities")
    meals = [
        [f"Day 1 lunch compensation (arrival before {fmt_t(LUNCH_BEFORE)})", len(lunch),
         f"GEL {len(lunch) * LUNCH_GEL} ({LUNCH_GEL} x {len(lunch)})", ", ".join(mark(p) for p in lunch)],
        [f"Day 1 Mtskheta dinner (in Tbilisi by {fmt_t(MTSKHETA_DEPARTURE)})", len(dinner_ok), "",
         ", ".join(mark(p) for p in dinner_ok)],
        ["   misses the dinner (arrives after 16:00)", len(dinner_miss), "", ", ".join(
            f"{mark(p)} ({fmt_t(p['in']['arr'].time())})" for p in dinner_miss)],
        [f"Day 4 museum {fmt_t(MUSEUM_START)}-{fmt_t(MUSEUM_END)} (flight {fmt_t(MUSEUM_MIN_FLIGHT)} or later)",
         len(museum), vehicle_for(len(museum)) if museum else "", ", ".join(mark(p) for p in museum)],
    ]
    if excluded:
        meals.append(["Unknown (no ticket, not counted)", len(excluded), "", ", ".join(label(p) for p in excluded)])
    write(ws, r, ["Item", "Headcount", "Amount / vehicle", "Names"], meals)

    # sheet 3
    ws = wb.create_sheet("3 Coordinator")
    title(ws, 1, f"For the coordinator: special cases, not rebuilt automatically ({len(coord)} items)")
    ws.cell(2, 1, run_label).font = Font(italic=True, color="666666")
    write(ws, 3, ["ID", "Participant / room", "Case", "What was found", "Suggestion / note"], coord)
    for i, w in enumerate([12, 26, 40, 80, 60], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A4"

    path = os.path.join(out_dir, f"offsite_report_{tag}.xlsx")
    wb.save(path)

    # ----------------------------------------------------------------- console summary (ASCII only)
    room_guests = {room: [g["id"] for g in gs] for room, gs in rooms.items()}
    table_rows = {str(r.get("ID") or "").strip(): r for r in table}
    tab_itins = {}
    for pid, row in table_rows.items():
        built = itinerary_from_table(row, [])          # the table as the assistants filled it in
        if built:
            tab_itins[pid] = (built[0]["arr"], built[1]["dep"])
    real_itins = {p["id"]: (p["in"]["arr"], p["out"]["dep"]) for p in plan_people}
    A = kpis(tab_itins, room_guests, booked_by_room, set())
    B = kpis(real_itins, room_guests, booked_by_room, frozen_rooms)

    def vtxt(v):
        n, c = v
        return f"{n} (" + ", ".join(f"{c[k]} {k.split(' ')[0].lower()}" for k in
                                    ("Taxi", "Minibus (Sprinter)", "Bus") if c.get(k)) + ")"

    def canc(k):
        return f"{k['cancels']} ({'fits' if k['fits'] else 'OVER'} free limit {k['limit']})"

    lines = [
        ("Arrival transfers", vtxt(A["arr"]), vtxt(B["arr"])),
        ("Departure transfers", vtxt(A["dep"]), vtxt(B["dep"])),
        ("Mtskheta dinner, people", A["dinner"], B["dinner"]),
        ("Museum, people / vehicle", f"{A['museum'][0]} / {A['museum'][1].split(' ')[0].lower()}",
         f"{B['museum'][0]} / {B['museum'][1].split(' ')[0].lower()}"),
        ("Lunch compensation", f"{A['lunch']} / GEL {A['lunch'] * LUNCH_GEL}", f"{B['lunch']} / GEL {B['lunch'] * LUNCH_GEL}"),
        ("Hotel: room-to-room transfers", A["moves"], B["moves"]),
        ("Hotel: additions", A["adds"], B["adds"]),
        ("Hotel: cancellations", canc(A), canc(B)),
    ]

    filled_by = lambda pid: str((table_rows.get(pid) or {}).get("Filled in by") or "?").strip()

    # each case: who / short label / found / action / responsible assistant(s) / passengers by assistant
    cases = []

    def case(p, short, found, action, by_assistant=None):
        cases.append({"p": p, "short": short, "found": found, "action": action,
                      "resp": filled_by(p["id"]) if p else None, "by_assistant": by_assistant})

    for p in P.values():
        sp, hint = p["special"], "; ".join(hotel_hint.get(p["room"], []))
        if "no ticket" in sp:
            fb = filled_by(p["id"])
            plan = (f"planned UNCONFIRMED as {p['in']['flight']} {fmt_t(p['in']['arr'].time())} / "
                    f"{p['out']['flight']} {fmt_t(p['out']['dep'].time())}") if p["in"] else "NOT planned"
            case(p, "no ticket", f"no ticket; {plan}",
                 f"contact assistant {fb} (bought the ticket) and the participant: taking part? ticket "
                 f"exists? changed/returned it themselves?")
            continue
        segs = p["ticket"]["segments"]
        if "train" in sp or "route not Moscow-Moscow" in sp:
            route = " > ".join([segs[0]["frm"].split(" ")[0]] + [s["to"].split(" ")[0] for s in segs])
            case(p, "route with a train" if "train" in sp else "route not via Moscow",
                 f"route {route}{' incl. train' if 'train' in sp else ''}, arr "
                 f"{fmt_d(p['in']['arr'].date())[:5]} {fmt_t(p['in']['arr'].time())}",
                 "confirm the itinerary with the participant; update table" + (f"; {hint}" if hint else ""))
        elif "reissued" in sp:
            case(p, "reissued ticket", f"ticket reissued {fmt_d(p['ticket']['issued'])}: out {p['out']['flight']} "
                                       f"{fmt_t(p['out']['dep'].time())}",
                 "confirm the change, update table" + (f"; {hint}" if hint else ""))
        elif sp:
            case(p, ", ".join(sp), ", ".join(sp), "check manually" + (f"; {hint}" if hint else ""))
        if p["ticket"]["name_mismatch"]:
            case(p, "name on ticket", f"ticket name {p['ticket']['surname']}/{p['ticket']['name']} != passport",
                 "ask the carrier to correct the name to the passport spelling")
    handled = {"Route does not start/end in Moscow", "Route includes a train", "No ticket (UNCONFIRMED)",
               "Ticket reissued after the table was filled in", "Name on ticket differs from passport",
               "Hotel: special-case room not changed", "Carrier schedule change (applied automatically)"}
    other = [c for c in coord if c[2] not in handled]
    for n in notices:
        pax = [p for p in P.values() if p["ticket"] and any(s["notice"] is n for s in p["ticket"]["segments"])]
        groups = defaultdict(list)
        for p in pax:
            groups[filled_by(p["id"])].append(p)
        cases.append({"p": None, "short": f"{n['flight']} schedule change",
                      "found": f"{n['flight']} {fmt_d(n['date'])[:5]} now {fmt_t(n['now'][0])}-{fmt_t(n['now'][1])} "
                               f"(was {fmt_t(n['was'][0]) if n['was'] else '?'}-{fmt_t(n['was'][1]) if n['was'] else '?'}; "
                               f"{len(pax)} pax, not in table)",
                      "action": "assistants inform their passengers; already applied in the plan",
                      "resp": ", ".join(sorted(groups)), "by_assistant": dict(sorted(groups.items()))})
    for c in other:
        cases.append({"p": None, "short": c[2], "found": f"{c[1]}: {c[3]}", "action": c[4] or "check manually",
                      "resp": ", ".join(sorted({filled_by(x.strip()) for x in str(c[0]).split(",") if x.strip()}))
                      or None, "by_assistant": None})

    # headline: what changed vs the table, what needs a decision
    facts = [("arrival transfers", A["arr"][0], B["arr"][0], " vehicles"),
             ("departure transfers", A["dep"][0], B["dep"][0], " vehicles"),
             ("Mtskheta dinner", A["dinner"], B["dinner"], " people"),
             ("museum", A["museum"][0], B["museum"][0], " people"),
             ("lunch compensation", A["lunch"], B["lunch"],
              f" people (GEL {A['lunch'] * LUNCH_GEL:,} {{a}} {B['lunch'] * LUNCH_GEL:,})"),
             ("hotel room-to-room transfers", A["moves"], B["moves"], ""),
             ("hotel additions", A["adds"], B["adds"], ""),
             ("hotel cancellations", A["cancels"], B["cancels"], "")]
    # "{a}" = arrow placeholder: "->" in the console, a real arrow in Word
    changed = [f for f in facts if f[1] != f[2]]
    if changed:
        head1 = ("Compared with the assistants' table, the tickets and carrier notices change "
                 + "; ".join(f"{n} {a} {{a}} {b}{u}" for n, a, b, u in changed) + ".")
        if notices:
            head1 += (" Main cause: carrier schedule changes on " + " and ".join(n["flight"] for n in notices)
                      + " that were never entered in the table.")
    else:
        head1 = "The tickets and carrier notices change none of the key indicators."
    hotel_decisions = [h for p in P.values() for h in hotel_hint.get(p["room"], []) if p["special"]]
    hotel_decisions = list(dict.fromkeys(hotel_decisions))
    hotel_txt = (f"Hotel: {B['moves']} room-to-room transfer(s), {B['adds']} addition(s), {B['cancels']} "
                 f"cancellation(s) - {'within' if B['fits'] else 'OVER'} the free-cancellation limit.")
    who_short = lambda c: (f"{c['p']['surname'].title()} ({c['short']})" if c["p"] else c["short"])
    head2 = ((f"{len(cases)} cases: " + ", ".join(who_short(c) for c in cases) + "."
              + (" Hotel decisions: " + "; ".join(hotel_decisions) + "." if hotel_decisions else ""))
             if cases else "No special cases.")
    frozen_note = (f"Special-case rooms {', '.join(sorted(frozen_rooms))} are not changed automatically."
                   if frozen_rooms else "")

    # ---- console (ASCII only)
    asc = lambda s: str(s).encode("ascii", "replace").decode()
    print(asc(f"OFFSITE CHECK  Tbilisi {fmt_d(DAY1)[:5]}-{fmt_d(LAST_DAY)}  (today {fmt_d(TODAY)})"))
    print(asc(run_label))
    print(asc(f"Table errors: {len(errors)} differences in {len({e[0] for e in errors})} participants"))
    print(f"{'Indicator':<31}{'Assistants table':<32}->  Tickets + notices")
    for name, a, b in lines:
        print(asc(f"{name:<31}{str(a):<32}->  {b}"))
    if frozen_note:
        print(asc("  (* " + frozen_note + ")"))
    print(f"SPECIAL CASES ({len(cases)})")
    for c in cases:
        who = f"{c['p']['id']} {c['p']['surname']}" if c["p"] else "Carrier"
        resp = f" [assistant {c['resp']}]" if c["resp"] else ""
        print(asc(f"- {who}{resp}: {c['found']}"))
        print(asc(f"    -> {c['action']}"))
        for a, ps in (c["by_assistant"] or {}).items():
            print(asc(f"       {a}: " + ", ".join(p["surname"] for p in ps)))

    # ---- Word summary
    docx_path = write_docx(out_dir, head1, head2, hotel_txt, frozen_note, lines, cases, errors, path,
                           tag, run_label)
    print(asc(f"Excel: {path}"))
    print(asc(f"Word : {docx_path}"))
    return path


def write_docx(out_dir, head1, head2, hotel_txt, frozen_note, lines, cases, errors, xlsx_path, tag, run_label):
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt, RGBColor, Cm

    doc = Document()
    zoom = doc.settings.element.find(qn("w:zoom"))   # python-docx template omits the required w:percent
    if zoom is not None and zoom.get(qn("w:percent")) is None:
        zoom.set(qn("w:percent"), "100")
    sec = doc.sections[0]
    sec.left_margin = sec.right_margin = Cm(2)
    sec.top_margin = sec.bottom_margin = Cm(1.8)
    base = doc.styles["Normal"]
    base.font.name, base.font.size = "Calibri", Pt(11)
    base.paragraph_format.space_after = Pt(4)
    for st, size in (("Title", 18), ("Heading 1", 13)):
        s = doc.styles[st]
        s.font.name, s.font.size, s.font.bold = "Calibri", Pt(size), True
        s.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
        s.paragraph_format.space_before = Pt(10 if st != "Title" else 0)
        s.paragraph_format.space_after = Pt(4)
        s.paragraph_format.keep_with_next = True

    def shade(cell, hex_fill):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), hex_fill)
        tcPr.append(shd)

    def para(text="", bold_prefix=None, style=None, size=None, color=None):
        p = doc.add_paragraph(style=style)
        if bold_prefix:
            r = p.add_run(bold_prefix)
            r.bold = True
        r = p.add_run(text)
        if size:
            r.font.size = Pt(size)
        if color:
            r.font.color.rgb = RGBColor.from_string(color)
        return p

    doc.add_paragraph(f"Offsite Tbilisi {fmt_d(DAY1)[:5]}-{fmt_d(LAST_DAY)}: re-check of tickets and plan", style="Title")
    para(f"{run_label}. Status as of {fmt_d(TODAY)}. Sources: e-tickets, carrier notices, participant list, hotel plan; "
         f"checked against the assistants' table ({len(errors)} differences in "
         f"{len({e[0] for e in errors})} participants).", size=9, color="666666")
    para(head1.replace("{a}", "→"), bold_prefix="What changed. ")
    para(head2, bold_prefix="Needs action. ")

    doc.add_paragraph("Key indicators", style="Heading 1")
    t = doc.add_table(rows=1, cols=3)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    widths = (Cm(6.0), Cm(5.5), Cm(5.5))
    for i, h in enumerate(("Indicator", "Assistants' table", "Tickets + notices")):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        r.bold, r.font.color.rgb = True, RGBColor(0xFF, 0xFF, 0xFF)
        shade(c, "305496")
    for name, a, b in lines:
        row = t.add_row().cells
        row[0].text, row[1].text = name, str(a)
        r = row[2].paragraphs[0].add_run(str(b))
        if str(a) != str(b):
            r.bold = True
            shade(row[2], "FFF2CC")
    for row in t.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = w
            row.cells[i].paragraphs[0].paragraph_format.space_after = Pt(0)
    para(hotel_txt + (" " + frozen_note if frozen_note else "") + " Changed values are highlighted.",
         size=9, color="666666")

    doc.add_paragraph("Special cases and next actions", style="Heading 1")
    for i, c in enumerate(cases, 1):
        who = (f"{c['p']['id']} {c['p']['surname'].title()} {c['p']['name'].title()}" if c["p"] else "Carrier")
        p = doc.add_paragraph(style="List Number")
        p.paragraph_format.keep_with_next = True
        r = p.add_run(f"{who}: {c['short']}")
        r.bold = True
        if c["resp"]:
            r = p.add_run(f"  |  responsible: assistant {c['resp']}")
            r.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
        q = para(c["found"][0].upper() + c["found"][1:], bold_prefix="Found: ")
        q.paragraph_format.left_indent = Cm(0.63)
        q = para(c["action"][0].upper() + c["action"][1:], bold_prefix="Next action: ")
        q.paragraph_format.left_indent = Cm(0.63)
        for a, ps in (c["by_assistant"] or {}).items():
            b = doc.add_paragraph(style="List Bullet 2")
            r = b.add_run(f"Assistant {a} ({len(ps)}): ")
            r.bold = True
            b.add_run(", ".join(f"{x['surname'].title()} {x['name'].title()}" for x in ps))
            b.paragraph_format.space_after = Pt(0)

    para(f"Full details: {os.path.basename(xlsx_path)} (sheets: 1 Table errors, 2 Corrected plan, 3 Coordinator).",
         size=9, color="666666").paragraph_format.space_before = Pt(8)

    path = os.path.join(out_dir, f"offsite_summary_{tag}.docx")
    doc.save(path)
    return path


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    elif os.path.exists(os.path.join(here, "participants.xlsx")):
        folder = here
    else:
        folder = os.path.join(here, "sample")   # the published fictional sample
    run(os.path.abspath(folder))
