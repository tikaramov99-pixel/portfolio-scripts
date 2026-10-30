"""
Normalize every ledger export in a folder so that it can be read and printed.

Each file is a quarterly VAT ledger extract from the same reporting system:
a header block (rows 1 - 12: a title, then label / value pairs), 3 rows of
column headers (13 - 15) and the entries from row 16 down, with dozens of
columns which stay empty for every entry and merged cells everywhere.
For each file the script:

  1. unmerges all cells and saves the header block (A1 - A12 and F2 - F12);
  2. deletes every column which is empty from row 16 down;
  3. clears the header area and writes the header block back into merged
     blocks (title across A - O, labels across A - F, values across G - L);
  4. removes the total row of an earlier run, then adds a new bold total
     under the column named in SUM_HEADER_TEXT (format 1,234,567.89);
  5. sets 8 pt with text wrap everywhere, clears row 13, makes rows 14 - 15 bold;
  6. in Excel itself: A4 landscape with the margins below, text in rows 13 and
     15 turned sideways, AutoFit of columns and rows, 1 page wide when printed.

Step 6 needs Windows with Microsoft Excel (pywin32); openpyxl cannot do a real
AutoFit, which is why the last step runs in Excel. The files are changed in
place, so run the script once, on a copy of the folder with fresh exports:
a second run reads the header values from column F, where they no longer are.

Written with ChatGPT in January 2026 (see README.md).
Requires openpyxl, and pywin32 on Windows (pip install openpyxl pywin32).
"""
import sys
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill

# ----------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------
FOLDER_PATH = Path(__file__).parent / "sample" / "ledgers"
START_DATA_ROW = 16
SUM_HEADER_TEXT = "RUB (line 160)"   # part of the header of the column to total
FONT_SIZE = 8
LEFT_RIGHT_MARGIN_CM = 0.64
TOP_BOTTOM_MARGIN_CM = 1.91


# ----------------------------------------------------------------------
# Step 1 - 5: openpyxl
# ----------------------------------------------------------------------
def clear_header_area(ws):
    for r in range(1, 13):
        for c in range(1, ws.max_column + 1):
            cell = ws.cell(r, c)
            cell.value = None
            cell.fill = PatternFill()
            cell.border = Border()
            cell.font = Font(size=FONT_SIZE)
            cell.alignment = Alignment(wrap_text=True)


def clear_row_formatting(ws, row):
    for c in range(1, ws.max_column + 1):
        cell = ws.cell(row, c)
        cell.fill = PatternFill()
        cell.border = Border()


def preprocess_file(path: Path):
    wb = load_workbook(path)
    for ws in wb.worksheets:
        # unmerge everything
        for m in list(ws.merged_cells.ranges):
            ws.unmerge_cells(str(m))

        # save the header block before any change to the structure
        header_A = {r: ws.cell(r, 1).value for r in range(1, 13)}
        header_F = {r: ws.cell(r, 6).value for r in range(2, 13)}

        # delete the columns which are empty from row 16 down
        max_row = ws.max_row
        cols_to_delete = []
        for c in range(1, ws.max_column + 1):
            if all(
                ws.cell(r, c).value in (None, "")
                for r in range(START_DATA_ROW, max_row + 1)
            ):
                cols_to_delete.append(c)
        for c in reversed(cols_to_delete):
            ws.delete_cols(c)

        # clear the header area and write the header block back
        clear_header_area(ws)
        ws.cell(1, 1).value = header_A.get(1)
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=15)
        for r in range(2, 13):
            ws.cell(r, 1).value = header_A.get(r)
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
            ws.cell(r, 7).value = header_F.get(r)
            ws.merge_cells(start_row=r, start_column=7, end_row=r, end_column=12)

        # remove the total of an earlier run (the bold last row)
        last_row = ws.max_row
        for c in range(1, ws.max_column + 1):
            cell = ws.cell(last_row, c)
            if cell.font and cell.font.bold:
                ws.delete_rows(last_row)
                break

        # total under the column named in SUM_HEADER_TEXT
        target_col = None
        for r in range(1, START_DATA_ROW):
            for c in range(1, ws.max_column + 1):
                v = ws.cell(r, c).value
                if isinstance(v, str) and SUM_HEADER_TEXT in v:
                    target_col = c
                    break
            if target_col:
                break

        sum_cell = None
        if target_col:
            total = 0
            for r in range(START_DATA_ROW, ws.max_row + 1):
                v = ws.cell(r, target_col).value
                if isinstance(v, (int, float)):
                    total += v
            sum_cell = ws.cell(ws.max_row + 1, target_col)
            sum_cell.value = total
            sum_cell.number_format = "#,##0.00"

        # base font and text wrap
        for r in range(1, ws.max_row + 1):
            for c in range(1, ws.max_column + 1):
                ws.cell(r, c).font = Font(size=FONT_SIZE)
                ws.cell(r, c).alignment = Alignment(wrap_text=True)

        # row 13 without fill and borders, rows 14 - 15 bold
        clear_row_formatting(ws, 13)
        for r in (14, 15):
            for c in range(1, ws.max_column + 1):
                ws.cell(r, c).font = Font(size=FONT_SIZE, bold=True)

        # the total stays bold
        if sum_cell:
            sum_cell.font = Font(size=FONT_SIZE, bold=True)

    wb.save(path)


# ----------------------------------------------------------------------
# Step 6: Excel (COM)
# ----------------------------------------------------------------------
def excel_finalize(folder: Path):
    import win32com.client as win32

    excel = win32.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    for xlsx in folder.glob("*.xlsx"):
        wb = excel.Workbooks.Open(str(xlsx))
        path = str(xlsx)
        for ws in wb.Worksheets:
            ps = ws.PageSetup
            ps.Orientation = 2        # landscape
            ps.PaperSize = 9          # A4
            ps.LeftMargin = excel.CentimetersToPoints(LEFT_RIGHT_MARGIN_CM)
            ps.RightMargin = excel.CentimetersToPoints(LEFT_RIGHT_MARGIN_CM)
            ps.TopMargin = excel.CentimetersToPoints(TOP_BOTTOM_MARGIN_CM)
            ps.BottomMargin = excel.CentimetersToPoints(TOP_BOTTOM_MARGIN_CM)

            used_cols = ws.UsedRange.Columns.Count
            # text sideways in rows 13 and 15 only (row 14 stays horizontal)
            ws.Range(ws.Cells(13, 1), ws.Cells(13, used_cols)).Orientation = -90
            ws.Range(ws.Cells(15, 1), ws.Cells(15, used_cols)).Orientation = -90

            ws.Columns.AutoFit()
            ws.Rows.AutoFit()

            ps.Zoom = False
            ps.FitToPagesWide = 1
            ps.FitToPagesTall = 2
        wb.SaveAs(path)       # Save fails on these files, SaveAs to the same path works
        wb.Close(False)

    excel.Quit()


# ----------------------------------------------------------------------
# Run
# ----------------------------------------------------------------------
if __name__ == "__main__":
    for f in FOLDER_PATH.glob("*.xlsx"):
        preprocess_file(f)
    if sys.platform == "win32":
        excel_finalize(FOLDER_PATH)
    else:
        print("Step 6 skipped: it needs Windows with Microsoft Excel.")
