# 1. Rows of a Word table grouped by colour

**The task.** Every month the firm reported to its key client on 6 - 12 matters worked on by 5 - 7 lawyers, and the time entries for the report came as one Word table, in which the rows belonging together were marked with the same colour, and for the report they had to be put together, group by group.

**What the script does.** Word keeps a colour in 3 different places: as shading of the cell, as shading of the paragraph inside the cell, or as highlighter on the text itself, and the files I worked with used more than one of them at once. The script reads all 3 for every row, treats rows with the same set of colours as 1 group and writes a new document: the header row, then each group with 1 empty row before it and 4 after it, the rows inside a group in their original order and with their colours kept.

| Before | After |
| --- | --- |
| ![The table as it comes](images/before.png) | ![The same rows grouped](images/after.png) |

**How to run it.** `pip install python-docx`, then `python group_rows_by_highlight.py`: it reads `sample/billing_sample.docx` and writes `sample/billing_sample_grouped.docx`. The input has to be .docx, so an old .doc file is first saved as .docx in Word.

## How it was built

I described the table and the task, and the AI first explained that Word stores no "colour of a row" at all, then wrote a script grouping the rows by cell shading and highlighter. 2 problems were worth knowing about:

| What the test run showed | Why | What fixed it |
| --- | --- | --- |
| Only the uncoloured rows came together; the coloured ones stayed mixed | In these files the colour sat in a 3rd place, the shading of the paragraph inside the cell, which the script did not read | The script reads all 3 places and treats the set of colours as the key |
| Saving failed with "file not found" | The AI had doubled a folder in the output path | The path, which is now a setting at the top of the script |

Then the layout the report needed: 1 empty row before each group and 4 after it. This is the version I used for the monthly report from then on.

## Prepared for publication

The logic is unchanged. The paths point to the sample folder next to the script, the code runs from `main()`, the comments are in English, and the sample is fictional: the real table and its entries were confidential. In the new document the table keeps Word's default look, without borders and with equal columns, so the layout is finished by hand.
