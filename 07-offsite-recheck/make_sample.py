"""
Make the fictional documents for the offsite re-check case: 40 participants
(30 colleagues and 10 companions) of a 4-day offsite in Tbilisi, 18 - 21 March
2027, as of Sunday 14 March 2027.

Everything here is invented. Output, in sample/:
  participants.xlsx        the list with passport names, types and rooms
  tickets_and_transfers.xlsx  the assistants' shared table
  hotel_plan.xlsx          the current hotel plan, room by room
  tickets/*.pdf            the e-tickets as received (1 is missing)
  airline_notices/*.txt    2 schedule changes from the carrier
Run: python make_sample.py
"""
import random
from pathlib import Path

import openpyxl
from openpyxl.styles import Font
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

OUT = Path(__file__).parent / "sample"
random.seed(7)

# ---- people ---------------------------------------------------------------
SURNAMES = ["Orlov", "Belova", "Kuznetsov", "Volkova", "Sokolov", "Lebedeva",
            "Morozov", "Novikova", "Pavlov", "Fedorova", "Gromov", "Zaitseva",
            "Egorov", "Vinogradova", "Bogdanov", "Kiseleva", "Makarov",
            "Smirnova", "Antonov", "Tarasova", "Belyaev", "Romanova", "Gusev",
            "Komarova", "Titov", "Kovaleva", "Ilyin", "Frolova", "Danilov",
            "Medvedeva"]
FIRST = ["Pavel", "Anna", "Dmitry", "Elena", "Sergey", "Olga", "Andrey",
         "Tatiana", "Igor", "Natalia", "Kirill", "Svetlana", "Maxim", "Irina",
         "Artem", "Yulia", "Nikolay", "Mariya", "Roman", "Ekaterina", "Oleg",
         "Daria", "Vadim", "Ksenia", "Ilya", "Polina", "Denis", "Alina",
         "Viktor", "Sofia"]
COMPANIONS = [("Sorokina", "Marina"), ("Zhukov", "Alexey"), ("Kozlova", "Vera"),
              ("Nikitin", "Mikhail"), ("Popova", "Inna"), ("Kalinin", "Grigory"),
              ("Golubeva", "Lidia"), ("Sergeev", "Fedor"), ("Ershova", "Nina"),
              ("Lazarev", "Stepan")]

people = []  # id, surname, first, type, companion_of, room
for i in range(30):
    people.append([f"P{i+1:02d}", SURNAMES[i].upper(), FIRST[i].upper(),
                   "Colleague", "", f"R{101+i}"])
for i in range(10):
    host = people[i]
    sur, first = COMPANIONS[i]
    people.append([f"P{31+i:02d}", sur.upper(), first.upper(),
                   "Companion", host[0], host[5]])
P = {p[0]: p for p in people}

# ---- flights (as ticketed, before the carrier's changes) --------------------
FLIGHTS = {
    # code: (from, to, date, dep, arr)
    "NR 211": ("Moscow SVO", "Tbilisi TBS", "18.03.2027", "08:30", "12:45"),
    "NR 215": ("Moscow SVO", "Tbilisi TBS", "18.03.2027", "16:35", "20:50"),
    "NR 219": ("Moscow VKO", "Tbilisi TBS", "18.03.2027", "16:05", "20:20"),
    "GA 702": ("Moscow VKO", "Tbilisi TBS", "17.03.2027", "19:25", "23:40"),
    "AY 318": ("Yerevan EVN", "Tbilisi TBS", "18.03.2027", "04:20", "05:10"),
    "AY 301": ("Moscow SVO", "Yerevan EVN", "17.03.2027", "22:55", "02:10"),
    "PQ 145": ("Moscow DME", "Tbilisi TBS", "18.03.2027", "06:05", "10:20"),
    "PQ 147": ("Moscow DME", "Tbilisi TBS", "18.03.2027", "08:45", "13:00"),
    "AY 140": ("Sochi AER", "Yerevan EVN", "18.03.2027", "14:10", "16:05"),
    "AY 322": ("Yerevan EVN", "Tbilisi TBS", "18.03.2027", "18:50", "19:40"),
    "NR 216": ("Tbilisi TBS", "Moscow SVO", "21.03.2027", "14:00", "16:20"),
    "NR 218": ("Tbilisi TBS", "Moscow SVO", "21.03.2027", "23:30", "01:50"),
    "PQ 150": ("Tbilisi TBS", "Moscow DME", "21.03.2027", "17:40", "20:05"),
}

def ids(a, b):
    return [f"P{i:02d}" for i in range(a, b + 1)]

INBOUND = {}
for pid in ["P01", "P31"]: INBOUND[pid] = ["GA 702"]
for pid in ["P02", "P32"]: INBOUND[pid] = ["AY 301", "AY 318"]
for pid in ["P12", "P13"]: INBOUND[pid] = ["PQ 145"]
for pid in ["P03", "P33"]: INBOUND[pid] = ["PQ 147"]
INBOUND["P14"] = ["NR 219"]
INBOUND["P15"] = ["RAIL", "AY 140", "AY 322"]   # the hearing city: special case
for pid in ids(4, 7) + ids(34, 37) + ids(16, 25): INBOUND[pid] = ["NR 211"]
for pid in ids(8, 10) + ids(38, 40) + ids(26, 30) + ["P11"]: INBOUND[pid] = ["NR 215"]

OUTBOUND = {}
for pid in ids(4, 7) + ids(34, 37) + ids(16, 21) + ["P26"]: OUTBOUND[pid] = "NR 216"
OUTBOUND["P22"] = "NR 218"   # changed by himself: the ticket says 218, the table 216
OUTBOUND["P12"] = "PQ 150"
for pid in P:
    OUTBOUND.setdefault(pid, "NR 218")
assert len(INBOUND) == 40 and len(OUTBOUND) == 40

MISSING_TICKET = "P27"
TICKET_NAME = {"P18": ("SMIRNOVA", "MARIIA")}   # passport says MARIYA
FARE = {pid: random.choice(range(28400, 41200, 100)) for pid in P}

# ---- the assistants' table: what it says ------------------------------------
def arrival_of(pid):
    f = FLIGHTS[INBOUND[pid][-1]]
    return f[2], f[4]

def table_rows():
    rows = []
    for pid, sur, first, typ, comp, room in people:
        inbound = INBOUND[pid][-1]
        d_in, t_in = arrival_of(pid)
        outbound = OUTBOUND[pid]
        price = FARE[pid] if typ == "Colleague" else None
        if pid == "P22":                      # not told to anyone else
            outbound = "NR 216"
        if pid == "P24":                      # typed in from the wrong flight
            inbound, d_in, t_in = "NR 215", "18.03.2027", "20:50"
        if pid == "P19":                      # 1,100 more than the ticket
            price += 1100
        if pid == "P15":                      # still the plan before the hearing
            inbound, d_in, t_in = "GA 702", "17.03.2027", "23:40"
        f_out = FLIGHTS[outbound]
        by = "A" if int(pid[1:]) <= 13 or typ == "Companion" else ("B" if int(pid[1:]) <= 24 else "C")
        rows.append([pid, f"{sur} {first}".title(), typ, inbound, d_in, t_in,
                     outbound, f_out[2], f_out[3], price, by])
    return rows

# ---- the hotel plan: what is booked ------------------------------------------
def hotel_rows():
    rows = []
    for i in range(30):
        room = f"R{101+i}"
        guests = [p[0] for p in people if p[5] == room]
        extra = early = late = "No"
        if room in ("R101", "R115"):        # R115: booked before the hearing
            extra = "Yes"
        if room in ("R113", "R104"):        # R104: never needed
            early = "Yes"
        late_rooms = {"R101", "R102", "R103", "R108", "R109", "R110", "R111",
                      "R113", "R114", "R115", "R121", "R123", "R124", "R125",
                      "R127", "R128", "R129", "R130"}   # R121 wrong; R112, R122 missing
        if room in late_rooms:
            late = "Yes"
        rows.append([room, ", ".join(guests), "18.03.2027", "21.03.2027",
                     extra, early, late])
    return rows

# ---- writers ---------------------------------------------------------------
def save_xlsx(path, title, header, rows, widths):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title
    ws.append(header)
    for c in ws[1]:
        c.font = Font(bold=True)
    for r in rows:
        ws.append(r)
    for col, w in zip("ABCDEFGHIJK", widths):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A2"
    wb.save(path)


def ticket_pdf(pid):
    sur, first = TICKET_NAME.get(pid, (P[pid][1], P[pid][2]))
    path = OUT / "tickets" / f"eticket_{sur}_{first}.pdf".replace(" ", "_")
    c = canvas.Canvas(str(path), pagesize=A4)
    y = 800
    def line(text, size=10, gap=16, bold=False):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(50, y, text)
        y -= gap
    line("ELECTRONIC TICKET ITINERARY RECEIPT", 14, 26, True)
    line(f"Passenger: {sur}/{first}", 11, 18, True)
    line(f"Ticket number: 555-{random.randint(2400000000, 2499999999)}")
    line(f"Booking reference: {''.join(random.choices('ABCDEFGHJKLMNPRSTUVWXYZ23456789', k=6))}")
    issued = "05.03.2027 (REISSUED)" if pid == "P22" else "02.02.2027"
    line(f"Issued: {issued}", gap=24)
    line("Flight     From            To              Date        Dep    Arr", bold=True)
    segments = INBOUND[pid] + [OUTBOUND[pid]]
    for code in segments:
        if code == "RAIL":
            line("TRAIN 104C  Krasnodar       Sochi           18.03.2027  05:40  10:15")
            continue
        f = FLIGHTS[code]
        line(f"{code:<10} {f[0]:<15} {f[1]:<15} {f[2]}  {f[3]}  {f[4]}")
    y -= 10
    if P[pid][3] == "Colleague":
        line(f"Fare: RUB {FARE[pid]:,}".replace(",", " "), 11, 18, True)
        line("Form of payment: invoice, ART-ORG corporate account")
    else:
        line(f"Fare: RUB {FARE[pid]:,}".replace(",", " "), 11, 18, True)
        line("Form of payment: card, paid by the passenger")
    if pid == "P15":
        y -= 10
        line("Rail segment: separate rail ticket attached by the passenger.")
    c.save()


NOTICES = {
    "2027-03-09_NR211_schedule_change.txt":
        "From: Northern Air <noreply@northernair.example>\n"
        "Date: 9 March 2027\nSubject: Schedule change NR 211, 18 March 2027\n\n"
        "Dear passenger,\n\nThe schedule of your flight NR 211 Moscow SVO - Tbilisi TBS "
        "on 18 March 2027 has changed.\nWas: departure 08:30, arrival 12:45.\n"
        "Now: departure 10:20, arrival 14:35.\n\nAll passengers on this flight are "
        "affected. No action is needed if the new time suits you.\n",
    "2027-03-11_NR216_schedule_change.txt":
        "From: Northern Air <noreply@northernair.example>\n"
        "Date: 11 March 2027\nSubject: Schedule change NR 216, 21 March 2027\n\n"
        "Dear passenger,\n\nThe schedule of your flight NR 216 Tbilisi TBS - Moscow SVO "
        "on 21 March 2027 has changed.\nWas: departure 14:00, arrival 16:20.\n"
        "Now: departure 11:10, arrival 13:30.\n\nAll passengers on this flight are "
        "affected. No action is needed if the new time suits you.\n",
}


def main():
    (OUT / "tickets").mkdir(parents=True, exist_ok=True)
    (OUT / "airline_notices").mkdir(exist_ok=True)
    save_xlsx(OUT / "participants.xlsx", "Participants",
              ["ID", "Surname (passport)", "Name (passport)", "Type", "Companion of", "Room"],
              people, (6, 20, 16, 12, 14, 8))
    save_xlsx(OUT / "tickets_and_transfers.xlsx", "Tickets and transfers",
              ["ID", "Name", "Type", "Inbound flight", "Arrival date", "Arrival time",
               "Outbound flight", "Departure date", "Departure time",
               "Ticket price, RUB (firm-paid)", "Filled in by"],
              table_rows(), (6, 22, 12, 14, 12, 12, 15, 14, 14, 16, 12))
    save_xlsx(OUT / "hotel_plan.xlsx", "Hotel plan",
              ["Room", "Guests", "Check-in", "Check-out", "Extra night 17.03",
               "Early check-in", "Late check-out"],
              hotel_rows(), (8, 14, 12, 12, 16, 15, 15))
    for pid in P:
        if pid != MISSING_TICKET:
            ticket_pdf(pid)
    for name, text in NOTICES.items():
        (OUT / "airline_notices" / name).write_text(text, encoding="utf-8")
    print(f"Saved to {OUT}")


if __name__ == "__main__":
    main()
