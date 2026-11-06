# 6. A register of acceptance certificates, checked by a second pass (September 2024)

**The task.** From 2022 the litigation practice I worked for ran one very large bankruptcy case: thousands of creditors, thousands of claims, and the attachments to those claims ran into tons of paper. Analysing them was what made me look for unusual solutions, and this script was one of the first: about 6 weeks after my first, very simple one, I was already trying it on a problem of this size. One of the attachments was 1 long Word document with the text of acceptance certificates, one after another, and the register had to be made from it: a table with the date, the number and the amount of every certificate. The number and the date stand in the header of each certificate ("Acceptance Certificate No. ... dated ..."), the amount in 1 line further down ("The cost of services under this Certificate is ... RUB"). Many certificates took several pages, the longest about 15. The headers and the amount lines had typos, and the amounts were not always written the same way.

**What the script does.** It goes through the document in 2 independent passes. Pass 1 reads it as a person would: a line which resembles the header (a fuzzy match, so a typo does not stop it) gives the number and the date, and the next line which resembles the amount line gives the amount. Pass 2 ignores all of that and looks only for certificate numbers: 10 digits in a row, with the letter O accepted where a 0 should be. Every number which pass 2 sees and pass 1 missed is printed, and its date and amount are taken from the text after it, up to the next certificate. The register gets every certificate from both passes, with a column saying which pass found it; a certificate whose amount could not be read gets an empty cell and is listed for checking by hand.

The idea of the second pass was mine, after 4 rounds of making pass 1 cleverer had not found all the certificates: rather than one more improvement to the search, an independent count to check the search against. It is the same principle as in the other cases here: the script should say what it did not find, not hide it.

This is one of my early scripts, from September 2024 (the very first one, on 7 August 2024, only listed the files in a folder).

## Run it yourself

1. `pip install python-docx pdfplumber fuzzywuzzy openpyxl`
2. `python extract_acts.py`. It reads `sample/acts.docx`, 14 fictional certificates in 1 Word file, 2 of them over 100 paragraphs long, and writes `sample/acts_register.xlsx`.
3. What comes out: pass 1 finds 12 certificates; pass 2 adds 2024000105, whose header has a typo and no space after "No.", and 2024000110, whose number has the letter O instead of the final 0. 2 certificates are listed for checking by hand: 2024000110, whose amount is given only in an annex, and 2024000112, whose amount line is worded differently from the rest. Both cells stay empty rather than take an amount from somewhere else.

`python extract_acts.py file.pdf` reads a PDF with a text layer instead. `python make_sample.py` makes the sample document again.

## How it was built

A ChatGPT chat in September 2024. The AI could not see the document or my computer: I described the task and the document, ran every version on the real file and brought back what came out.

| Round | What the run showed | What fixed it |
| --- | --- | --- |
| 1 | The first version found 3 times fewer amounts than numbers and dates | The table moved to Excel, and the amount search was reworked |
| 2 | Still not all the certificates | I asked for several rounds of search, each one looking for the certificates not found before. The AI made each round only lower the fuzzy threshold, and it did not help |
| 3 | The best of the versions so far missed only a couple of certificates, the long 15-page ones | I gave that version back to the AI as the base for the next ones |
| 4 | The next version took wrong amounts and still missed certificates. Some amounts had their thousands separated by spaces | The amount pattern accepts spaces between the thousands |
| 5 | Better, but still not all the certificates | My rule: a second pass looking only for the numbers, 10 digits in a row, with O allowed in place of 0; compare its list with pass 1 and print what pass 1 missed |
| 6 | The missing numbers were now known, without their dates and amounts | My rule: after such a number come its date and its amount, and only then the next number. This was the version that found all the certificates in the document |

After that the same script was moved to PDF files with a text layer, and then to scanned PDFs of 100 - 200 pages each, some of them scanned askew, which first had to be recognised. That part took most of the chat: Acrobat could not be started from a script, the 2 programs the next approach needed, Poppler and Tesseract, were not found by Windows until their folders were added to the PATH (the same problem I met again in November 2026, installing Claude Code), the next one was far too slow for documents of this size, and the last one ran with the pages recognised in parallel, inside a script which went through the whole folder and reported OK or failure for each step. The chat ends with that version, and I no longer remember for certain how it did on the whole folder, so the recognition step is not published here; the register is the part worth showing in any case.

## Prepared for publication

The case, the parties and the documents are not named; the sample is invented and in English, so the phrases the script looks for are English settings at the top (the real ones were Russian). The paths are settings; the amounts go into the table as numbers rather than text; the register gets the "Found by" column, and a certificate without an amount is written with an empty cell and listed, where in 2024 it was left out. The splitting of the document into chunks of 2,000 paragraphs, which I asked for in round 1, had already gone from the version I used.

3 problems are fixed here and marked `FIX` in the code. All 3 showed up when the 2024 logic was run on the fictional sample for this page:

1. A number with a letter in it was cut at the letter: pass 1 read "202400011O" as "202400011", and that cut number went into the register as a separate certificate, with the amount of the next one.
2. Pass 1 stopped looking for headers until it had found an amount. So a certificate whose amount line it could not read took the amount of the next certificate, and the next one was lost to pass 1. On the sample, 2024000112 got the amount of 2024000113. Now a new header closes the previous certificate.
3. For a number found only by pass 2, the amount was looked for to the end of the document, so a certificate without an amount took the amount of the one after it: 2024000110 got the amount of 2024000111. Now the search stops at the next certificate.
