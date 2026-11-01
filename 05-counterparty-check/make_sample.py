"""
Make the fictional table for the demo: 10 counterparties by name and tax ID,
some of them under an old name, as such a list usually is after a few years.

Everything here is invented. The local service page in sample/mock_service
knows 9 of these tax IDs; the 10th is not there on purpose.
Run: python make_sample.py  ->  sample/counterparties.xlsx
"""
from pathlib import Path

import openpyxl
from openpyxl.styles import Font

OUT = Path(__file__).parent / "sample" / "counterparties.xlsx"

ROWS = [  # name as it stands in the list, tax ID
    ("Northwind Trade LLC", "7701000013"),
    ("Harbor Line Logistics LLC", "7702000026"),
    ("Greyfield Construction LLC", "7703000039"),
    ("Petrov I., sole trader", "770400004211"),
    ("Riverside Foods", "7705000052"),
    ("Altair Leasing LLC", "7706000065"),
    ("Old Mill Holdings LLC", "7707000078"),
    ("Smirnova A., sole trader", "770800008422"),
    ("Polar Star Shipping JSC", "7709000091"),
    ("Eastgate Supplies LLC", "7710000103"),
]


def main():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Counterparties"
    ws.append(["Name", "Tax ID", "Status"])
    for c in ws[1]:
        c.font = Font(bold=True)
    for name, tax_id in ROWS:
        ws.append([name, tax_id])
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 24
    OUT.parent.mkdir(exist_ok=True)
    wb.save(OUT)
    print(f"Written: {OUT}")


if __name__ == "__main__":
    main()
