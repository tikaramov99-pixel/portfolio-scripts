"""
Make the fictional document for the demo: 14 acceptance certificates for
services, one after another in 1 Word file, as the real ones were.

Everything here is invented. Some certificates carry the kind of defects the
real documents had, so that both passes have something to do:
  2024000103, 2024000114  long, 100+ paragraphs each
  2024000105  a typo in the header and no space after "No.", so the header
              does not match exactly
  2024000107  an amount with spaces between the thousands
  2024000109  typos in the amount line
  2024000110  the letter O instead of the final 0 in the number, and the
              amount given only in an annex
  2024000112  the amount line worded differently from the rest

Run: python make_sample.py  ->  sample/acts.docx
"""
from pathlib import Path

import docx

OUT = Path(__file__).parent / "sample" / "acts.docx"

AGREEMENT = "under Services Agreement No. 17/2023 dated 01.02.2023"
SERVICES = [
    "Consulting services, 3.5 hours",
    "Preparation of the monthly report, 6 hours",
    "Data processing services, 4 hours",
    "Technical support, 2.5 hours",
    "Account management, 1 hour",
]

# number as typed, date, amount line, number of service paragraphs, header
CERTIFICATES = [
    ("2024000101", "15.01.2024", "48 000,00", 5, None),
    ("2024000102", "31.01.2024", "72 500,00", 5, None),
    ("2024000103", "29.02.2024", "315 000,00", 120, None),
    ("2024000104", "05.03.2024", "21 000,00", 5, None),
    ("2024000105", "12.03.2024", "36 000,00", 5,
     "Acceptance Certifcate No.2024000105 dated 12.03.2024"),
    ("2024000106", "29.03.2024", "64 800,00", 5, None),
    ("2024000107", "30.04.2024", "1 250 000,00", 10, None),
    ("2024000108", "15.05.2024", "18 900,00", 5, None),
    ("2024000109", "31.05.2024", "84 000,00", 5, None),
    ("202400011O", "28.06.2024", None, 5, None),
    ("2024000111", "15.07.2024", "42 000,00", 5, None),
    ("2024000112", "31.07.2024", "56 700,00", 5, None),
    ("2024000113", "15.08.2024", "27 300,00", 5, None),
    ("2024000114", "30.08.2024", "468 000,00", 150, None),
]


def amount_line(number, amount):
    if amount is None:
        return "The cost of services under this Certificate is set out in Annex 1."
    if number == "2024000109":
        return f"The cost of servises under this Certifcate is {amount} RUB."
    if number == "2024000112":
        return f"Total: {amount} RUB, VAT not applicable."
    return f"The cost of services under this Certificate is {amount} RUB."


def main():
    d = docx.Document()
    for number, date, amount, n_services, header in CERTIFICATES:
        d.add_paragraph(header or f"Acceptance Certificate No. {number} dated {date}")
        d.add_paragraph(f"Moscow, {date}")
        d.add_paragraph(
            f"Northwind Trade LLC (the Client) and Greyfield Services LLC (the "
            f"Contractor) have drawn up this Certificate {AGREEMENT}.")
        d.add_paragraph("The Contractor has rendered and the Client has accepted "
                        "the following services:")
        for i in range(n_services):
            d.add_paragraph(f"{i + 1}. {SERVICES[i % len(SERVICES)]}")
        d.add_paragraph(amount_line(number, amount))
        d.add_paragraph("The Client has no claims as to the scope, quality "
                        "and timing of the services.")
        d.add_paragraph("For the Contractor ____________    For the Client ____________")
        d.add_paragraph("")
    OUT.parent.mkdir(exist_ok=True)
    d.save(OUT)
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
