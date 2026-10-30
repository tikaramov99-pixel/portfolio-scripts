"""
Group the rows of a Word table by the way they are highlighted.

The monthly time entries for one client came as a Word table in which each
group of entries was marked with its own colour. Word keeps such a colour in
3 different places (cell shading, paragraph shading, highlighter on the text),
and the files used more than one of them at once, so the script reads all 3,
puts rows marked the same way into one group and writes a new document:
the header row, then every group with 1 empty row before it and 4 after it,
the rows inside a group staying in their original order.

Written with ChatGPT in January 2026, in 10 rounds (see README.md).
Requires python-docx (pip install python-docx); the input must be .docx.
"""
from collections import defaultdict
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

HERE = Path(__file__).parent
INPUT_PATH = HERE / "sample" / "billing_sample.docx"
OUTPUT_PATH = HERE / "sample" / "billing_sample_grouped.docx"


def cell_fill(cell):
    """Shading of the whole cell (Table -> Shading)."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.find(qn("w:shd"))
    if shd is not None:
        return shd.get(qn("w:fill"))
    return None


def paragraph_fill(paragraph):
    """Shading of a paragraph inside the cell (Borders and Shading -> Paragraph)."""
    pPr = paragraph._p.pPr
    if pPr is not None:
        shd = pPr.find(qn("w:shd"))
        if shd is not None:
            return shd.get(qn("w:fill"))
    return None


def run_highlight(run):
    """Highlighter on the text itself, or shading applied to the text."""
    if run.font.highlight_color:
        return str(run.font.highlight_color)
    rPr = run._r.rPr
    if rPr is not None:
        shd = rPr.find(qn("w:shd"))
        if shd is not None:
            return shd.get(qn("w:fill"))
    return None


def row_key(row):
    """Every colour found in the row, tagged with where Word keeps it."""
    fills = set()
    for cell in row.cells:
        cf = cell_fill(cell)
        if cf:
            fills.add(f"CELL:{cf}")
        for p in cell.paragraphs:
            pf = paragraph_fill(p)
            if pf:
                fills.add(f"PAR:{pf}")
            for r in p.runs:
                hf = run_highlight(r)
                if hf:
                    fills.add(f"RUN:{hf}")
    return tuple(sorted(fills)) or ("NO_FILL",)


def main():
    doc = Document(INPUT_PATH)
    table = doc.tables[0]

    groups = defaultdict(list)
    header = table.rows[0]
    for row in table.rows[1:]:
        groups[row_key(row)].append(row)

    new_doc = Document()
    new_table = new_doc.add_table(rows=1, cols=len(header.cells))
    for i, cell in enumerate(header.cells):
        new_table.rows[0].cells[i].text = cell.text

    def add_empty_rows(n):
        for _ in range(n):
            new_table.add_row()

    for rows in groups.values():
        add_empty_rows(1)
        for row in rows:
            new_row = new_table.add_row()
            for i, cell in enumerate(row.cells):
                new_cell = new_row.cells[i]
                new_cell._tc.clear_content()
                for el in cell._tc.iterchildren():
                    new_cell._tc.append(deepcopy(el))
        add_empty_rows(4)

    new_doc.save(OUTPUT_PATH)
    print(f"{len(groups)} groups written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
