"""
Put all quarterly ledger tables of a folder into one summary table.

From the first file the rows are taken from row 14 (the column headers and
the entries), from every next file from row 16 (the entries only). A double
line under the last row of each quarter keeps the quarters apart, the 2 header
rows are grey and bold, and a bold grand total goes under the column named in
SUM_HEADER_TEXT. Files are taken in the order of their names.

Written with ChatGPT in January 2026; 3 fixes made for publication in October
2026 are marked in the code (see README.md). Requires openpyxl.
"""
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Border, Font, PatternFill, Side

# ----------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------
SOURCE_FOLDER = Path(__file__).parent / "sample" / "ledgers"
OUT_FILE = SOURCE_FOLDER / "Summary.xlsx"
FIRST_TABLE_START_ROW = 14
NEXT_TABLES_START_ROW = 16
SUM_HEADER_TEXT = "RUB (line 160)"
FONT_SIZE = 8

double_side = Side(style="double")
double_border_bottom = Border(bottom=double_side)
header_fill = PatternFill(fill_type="solid", fgColor="D9D9D9")


def find_sum_column(ws):
    for r in range(1, 20):
        for c in range(1, ws.max_column + 1):
            v = ws.cell(r, c).value
            if isinstance(v, str) and SUM_HEADER_TEXT in v:
                return c
    return None


def copy_rows(src_ws, dst_ws, start_row, sum_col):
    for r in range(start_row, src_ws.max_row + 1):
        # fix for publication: a file processed by normalize_ledgers.py ends
        # with its own bold total, which is not an entry and is skipped
        if sum_col and r >= NEXT_TABLES_START_ROW and src_ws.cell(r, sum_col).font.bold:
            continue
        values = [src_ws.cell(r, c).value for c in range(1, src_ws.max_column + 1)]
        dst_ws.append(values)


def add_double_separator_below(ws, row):
    for c in range(1, ws.max_column + 1):
        ws.cell(row=row, column=c).border = double_border_bottom


def main():
    # fix for publication: the summary of an earlier run is not an input
    files = sorted(f for f in SOURCE_FOLDER.glob("*.xlsx") if f != OUT_FILE)
    if not files:
        raise RuntimeError("No .xlsx files in the folder")

    out_wb = Workbook()
    out_ws = out_wb.active
    out_ws.title = "Summary"

    sum_col_index = None
    first_table = True
    for i, file in enumerate(files):
        wb = load_workbook(file)
        ws = wb.active

        # the column to total is found once, in the first file
        if sum_col_index is None:
            sum_col_index = find_sum_column(ws)

        start_row = FIRST_TABLE_START_ROW if i == 0 else NEXT_TABLES_START_ROW

        # a double line under the last row of the previous quarter
        if not first_table:
            add_double_separator_below(out_ws, out_ws.max_row)

        copy_rows(ws, out_ws, start_row, sum_col_index)
        first_table = False

    # the 2 header rows: grey and bold
    for r in (1, 2):
        for c in range(1, out_ws.max_column + 1):
            cell = out_ws.cell(r, c)
            cell.fill = header_fill
            cell.font = Font(size=FONT_SIZE, bold=True)

    # grand total (fix for publication: from row 3, below the 2 header rows,
    # so that a column number in the header is not added to the sum)
    if sum_col_index:
        total = 0
        for r in range(3, out_ws.max_row + 1):
            v = out_ws.cell(r, sum_col_index).value
            if isinstance(v, (int, float)):
                total += v
        sum_cell = out_ws.cell(out_ws.max_row + 1, sum_col_index)
        sum_cell.value = total
        sum_cell.font = Font(size=FONT_SIZE, bold=True)
        sum_cell.number_format = "#,##0.00"

    # font for everything which is not bold already
    for r in range(1, out_ws.max_row + 1):
        for c in range(1, out_ws.max_column + 1):
            cell = out_ws.cell(r, c)
            if not cell.font or not cell.font.bold:
                cell.font = Font(size=FONT_SIZE)

    out_wb.save(OUT_FILE)
    print(f"{len(files)} tables put together in {OUT_FILE}")


if __name__ == "__main__":
    main()
