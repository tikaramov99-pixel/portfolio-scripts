# 2. Clean-up of VAT ledger exports (Excel)

**The task.** For one of the firm's matters I had 2 folders of quarterly VAT ledger extracts, the sales of one company and the purchases of another, all exported from the same reporting system: a header block, 3 rows of column headers, the entries, merged cells everywhere and many columns which stay empty for every entry. Each file had to become readable and printable on A4, with a total under the main amount column, and then each folder had to become 1 summary table with a grand total.

**What the scripts do.**

- `normalize_ledgers.py` goes through every file of a folder: it saves the header block, deletes the columns which are empty from the first entry down, writes the header back into merged blocks, adds a bold total in the format 1,234,567.89, sets 8 pt with text wrap, and then opens the file in Excel itself to turn the header text sideways, AutoFit columns and rows and fit the print to A4 landscape, 1 page wide.
- `consolidate_ledgers.py` puts the entries of all files of a folder into 1 table: grey bold header rows, a double line under the last row of each quarter and a bold grand total.

**How to run them.** Windows with Microsoft Excel, then `pip install openpyxl pywin32`. The fictional sample is in `sample/ledgers` (3 quarters of a company called Northwind). Make a copy of the folder, because `normalize_ledgers.py` changes the files in place, and run it once; then `python consolidate_ledgers.py` writes `Summary.xlsx` into the same folder. Without Windows the first script does everything except the Excel step and says so.

## The rounds with ChatGPT

40 rounds in 1 chat, here by stage.

| Rounds | Stage | What went wrong, and what fixed it |
| --- | --- | --- |
| 1 - 4 | Empty columns | The first script deleted the empty columns but wiped the header block and mixed up the column headers, because of the merged cells; unmerging first did not help, and only 1 sheet was processed. I specified the approach: cut the header block out first, delete the columns, then write the block back. |
| 5 - 9 | Header layout | The header text was too long for single cells, so I asked for merged blocks. 2 runs failed with "MergedCell is read-only", since values were written into cells already merged and the merges overlapped; the AI changed the order. After checking the original I corrected the layout twice (where the title goes, and that the values sit in column F, not B) and asked to clear the header formatting. |
| 10 - 12 | Print | A separate script for PDF in A4 landscape with all columns on 1 page wide. When I asked for all of it at once for the second folder, the AI gave only the export, so I asked for 1 run doing both, the clean-up first. |
| 13 - 25 | Total and widths | The bold total, the thousands separator and text wrap came quickly. Then 12 rounds on row heights and column widths: the AI first presented a row "autofit" which openpyxl cannot do, then a row autofit through Excel which did not work either, then computed column widths which still turned the numbers into "######" when printed, and only after several rounds of "it does not work" did it state that a real AutoFit of widths exists only in Excel. The last step moved into Excel itself. |
| 26 - 31 | The Excel step | I asked to turn the header text sideways to save width. 2 errors from Excel (orientation set on rows instead of a range, Save failing where SaveAs works) and 3 regressions which I caught: the total was no longer bold and was counted twice when the script ran again, the header values from column F disappeared, and after these fixes the script had stopped deleting the empty columns at all, which was the original task. |
| 32 - 34 | Header text | The header text disappeared completely. The AI's first explanation and fix changed nothing; the second put the steps in the right order (save the header, delete the columns, rebuild the header). Then 8 pt, rows 14 - 15 bold and row 13 cleared. |
| 35 - 40 | Second folder and the summary | The purchases folder with its own total column, and row 14 left horizontal. Then the summary script, its layout (grey bold header, double line under each quarter, no blank rows between quarters, bold grand total) and its version for the other folder. |

## Prepared for publication

The paths and the column to total are settings at the top of each script, the comments are in English, the Excel step is skipped outside Windows, and the sample is fictional: the real extracts were confidential.

3 problems of `consolidate_ledgers.py` are fixed here and marked in the code:

1. A file which has already been through `normalize_ledgers.py` ends with its own total, and the summary took that row as an entry, so the grand total came out twice the real one. I caught it at the final run in January and, rather than going one more round with the AI, corrected the total in the table by hand; here the script itself skips the rows with the bold total.
2. `Summary.xlsx` lies in the same folder and was read as one more input on a second run. It is now left out.
3. The grand total also added the column number from the second header row. It now counts from the first entry.

The last 2 showed up when both scripts were tested on the fictional sample for this page.

One limit of `normalize_ledgers.py` stays as it was: it is meant to run once, on fresh exports, because a second run looks for the header values in column F, where they no longer are.
