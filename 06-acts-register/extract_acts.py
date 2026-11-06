"""
Build a register of acceptance certificates (date, number, amount) from one
long document which holds the text of all of them, one after another.

September 2024: written by ChatGPT to my specification over 6 rounds for a
Word document, then moved to PDF with a text layer. Cleaned up for
publication in November 2026: settings at the top, English comments and
phrases, a fictional sample to run it on, and 3 fixes, marked "FIX" in the
code and listed in the README.

How it works, in 2 independent passes:
  1. Pass 1 goes through the document line by line. A line which resembles
     the certificate header (fuzzy match, so typos do not stop it) gives the
     number and the date; the next line which resembles the amount line gives
     the amount.
  2. Pass 2 ignores that logic and looks only for certificate numbers:
     10 digits in a row, with the letter O accepted in place of a final 0.
     Every number which pass 2 sees and pass 1 missed is reported, and its
     date and amount are looked for in the text after it, up to the next
     certificate.
The register gets every certificate from both passes, with a column saying
which pass found it.

Run on the fictional sample:
    pip install python-docx pdfplumber fuzzywuzzy openpyxl
    python extract_acts.py
"""
import re
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Font
from fuzzywuzzy import fuzz

HERE = Path(__file__).resolve().parent

# ---- Settings -------------------------------------------------------------

SOURCE = HERE / "sample" / "acts.docx"   # .docx, or .pdf with a text layer
OUTPUT = HERE / "sample" / "acts_register.xlsx"

# The real documents were in Russian: "Акт сдачи-приемки услуг № ... от ..."
# and "Стоимость услуг по данному Акту составляет ... руб."
HEADER_PHRASE = "Acceptance Certificate No."
# FIX 1: the number must end where the digits end. In 2024 "(\d+)" also
# matched the first 9 digits of a number with a letter in it, and such a
# certificate went into the register under a cut number.
HEADER_REGEX = re.compile(r"Acceptance Certificate No\. (\d+)\b")
AMOUNT_PHRASE = "The cost of services under this Certificate is"

FUZZY_HEADER = 75   # % similarity for a line to count as a header
FUZZY_AMOUNT = 65   # % similarity for a line to count as the amount line

DATE_REGEX = re.compile(r"\d{2}\.\d{2}\.\d{4}")
# Thousands may be separated by spaces: "1 250 000,00 RUB".
AMOUNT_REGEX = re.compile(r"(\d{1,3}(?:\s\d{3})*(?:[.,]\d+)?) RUB", re.IGNORECASE)
# Pass 2: a certificate number is 10 digits; a scan or a typist may turn the
# final 0 into the letter O.
NUMBER_REGEX = re.compile(r"\b(\d{9}[\dO])\b")

# ---------------------------------------------------------------------------


def read_lines(path):
    """The document as a list of lines: Word paragraphs, or PDF text lines."""
    if path.suffix.lower() == ".pdf":
        import pdfplumber
        lines = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                lines.extend((page.extract_text() or "").split("\n"))
    else:
        import docx
        lines = [p.text for p in docx.Document(path).paragraphs]
    return [line.strip() for line in lines]


def looks_like(line, phrase, threshold):
    return fuzz.partial_ratio(line, phrase) >= threshold


def to_amount(text):
    return float(text.replace(" ", "").replace(" ", "").replace(",", "."))


def pass_one(lines):
    """Header, then amount, certificate after certificate."""
    rows, seen = [], set()
    number = date = None

    for line in lines:
        if looks_like(line, HEADER_PHRASE, FUZZY_HEADER):
            m = HEADER_REGEX.search(line)
            d = DATE_REGEX.search(line)
            if m and d:
                # FIX 2: a new header closes the previous certificate. In 2024
                # the script stopped looking for headers until it had found an
                # amount, so a certificate whose amount line it could not read
                # took the amount of the next one, and the next one was lost.
                if number and (number, date) not in seen:
                    rows.append([date, number, None, "header, no amount"])
                    seen.add((number, date))
                number, date = m.group(1), d.group(0)
                continue

        if number and looks_like(line, AMOUNT_PHRASE, FUZZY_AMOUNT):
            m = AMOUNT_REGEX.search(line)
            if m:
                if (number, date) not in seen:
                    rows.append([date, number, to_amount(m.group(1)), "header"])
                    seen.add((number, date))
                number = date = None

    if number and (number, date) not in seen:
        rows.append([date, number, None, "header, no amount"])
    return rows


def pass_two_numbers(lines):
    """Every certificate number in a line which resembles a header."""
    found = {}
    for i, line in enumerate(lines):
        if looks_like(line, HEADER_PHRASE, FUZZY_HEADER):
            for m in NUMBER_REGEX.finditer(line):
                number = m.group(1)
                if number[-1] == "O":
                    number = number[:-1] + "0"
                found.setdefault(number, i)
    return found


def date_and_amount_after(lines, number, start, next_header):
    """The date and the amount which follow a number, before the next one."""
    date = amount = None
    for i, line in enumerate(lines[start:next_header]):
        if date is None:
            # The date is read from the header line itself, after the number;
            # in 2024 the search began on the next line.
            if i == 0:
                pos = line.replace("O", "0").find(number)
                line_part = line[pos + len(number):] if pos >= 0 else line
            else:
                line_part = line
            m = DATE_REGEX.search(line_part)
            if m:
                date = m.group(0)
        if amount is None:
            m = AMOUNT_REGEX.search(line)
            if m:
                amount = to_amount(m.group(1))
        if date and amount is not None:
            break
    return date, amount


def main():
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else SOURCE
    lines = read_lines(source)

    rows = pass_one(lines)
    numbers = pass_two_numbers(lines)

    known = {row[1] for row in rows}
    missing = [n for n in numbers if n not in known]
    header_lines = sorted(numbers.values())

    if missing:
        print("Found by pass 2 only: " + ", ".join(missing))
    for number in missing:
        start = numbers[number]
        # FIX 3: the search stops at the next certificate. In 2024 it ran to
        # the end of the document, so a certificate without an amount took
        # the amount of the one after it.
        later = [i for i in header_lines if i > start]
        end = later[0] if later else len(lines)
        date, amount = date_and_amount_after(lines, number, start, end)
        rows.append([date, number, amount, "pass 2"])

    rows.sort(key=lambda r: r[1])
    write_register(rows, OUTPUT)

    no_amount = [r[1] for r in rows if r[2] is None]
    print(f"Certificates in the register: {len(rows)} "
          f"(pass 1: {len(rows) - len(missing)}, pass 2 only: {len(missing)})")
    if no_amount:
        print("No amount found, check by hand: " + ", ".join(no_amount))
    print(f"Saved: {OUTPUT}")


def write_register(rows, path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Register"
    ws.append(["Date", "Certificate No.", "Amount, RUB", "Found by"])
    for c in ws[1]:
        c.font = Font(bold=True)
    for row in rows:
        ws.append(row)
    for r in ws.iter_rows(min_row=2, min_col=3, max_col=3):
        r[0].number_format = "# ##0.00"
    for col, width in zip("ABCD", (12, 18, 16, 20)):
        ws.column_dimensions[col].width = width
    wb.save(path)


if __name__ == "__main__":
    main()
