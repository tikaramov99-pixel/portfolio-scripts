# Working with AI: 4 scripts from 2024 - 2026, 2 cases from October 2026 and 1 from November 2026

From August 2024 until I left at the end of June 2026 I had AI write Python scripts for the tasks of a law firm in Moscow, where I worked in operations: about once every month and a half, starting half a year before the practice got its name, "vibe coding", in February 2025. I do not write code myself: my part was to describe the task and the files precisely enough, to run every version on the real files and to say exactly what came out wrong, until the result did what the task needed.

4 of those scripts are here: 2 of the early ones, from September and December 2024, and 2 from January 2026 (the very first, on 7 August 2024, did nothing more than list the files in a folder). All 4 are simple by today's standards. At the time, though, AI worked in a chat window and could not see my files or run anything: every version travelled from the chat to my computer and back, and the real work was in the checking.

Cases 3 and 4 are from October 2026 and show where this has gone since: one of my offsite procedures rewritten so that an AI agent working inside the workbook can follow it, under checkpoints; and the other end of the scale: a monthly check of a confidential file done entirely on 1 computer, with no internet and no AI involved at all, for the cases where nothing may leave the office even in theory.

Case 7, from November 2026, is the same kind of work done in Claude Code, which reads the files, runs the script and sees its own errors: one of my offsite routines, the re-check of the tickets and the whole plan after every change, built to my rules, with my part reduced to what it always really was: the rules, the answers to its questions and the checking.

All data in the samples is fictional. The real files were confidential and are not published; the scripts processed them on my own machine.

| Case | The task | Result |
| --- | --- | --- |
| [1. Rows grouped by colour](01-group-rows-by-highlight/) (January 2026) | Monthly time entries for the firm's key client: put together the rows of a Word table which are marked with the same colour | 1 script, used for the monthly report |
| [2. Ledger clean-up](02-ledger-cleanup/) (January 2026) | Folders of quarterly VAT ledger exports: delete the empty columns, rebuild the header, add the total, fit the print, then 1 summary table per folder | 2 scripts, used on 2 folders |
| [3. A playbook for a person or an AI agent](03-agent-playbook/) (October 2026) | The offsite playbook for a flight moved by the carrier, rewritten so that an AI agent connected to the workbook can follow it, stopping for the coordinator's approval | The playbook, 2 logged runs, and a 5-minute guide to run it yourself |
| [4. Confidential data, checked on 1 computer](04-offline-analysis/) (October 2026) | A month of lawyers' time entries checked before billing: duplicates, days over 10 hours, empty descriptions, wrong rates, matters over their cap | A program in 1 file which needs nothing but Python (the start file installs it if missing), only reads the file, and can be cut off from the internet with 1 tick box |
| [5. Counterparties checked by tax ID](05-counterparty-check/) (December 2024) | Several hundred counterparties: look each one up by tax ID in a public company-check service and write its current name and status into the table | 1 script which drives the browser, run once on the whole table, with a second pass for the pages which had not loaded |
| [6. A register of acceptance certificates](06-acts-register/) (September 2024) | 1 long document with the text of all the certificates, typos included: a table with the date, the number and the amount of each | 1 script with 2 independent passes, the second one checking the first and printing what it missed |
| [7. An offsite plan re-checked after every change](07-offsite-recheck/) (November 2026) | 40 participants, 3 assistants filling in 1 table, flights moved by the carrier and changes nobody passed on: check the table against the tickets and rebuild transfers, hotel changes and headcounts by my rules | A script written and run by Claude Code to my rules, in 4 rounds of my answers and corrections, with a report in the window, in Excel and in Word |

## How I worked with the AI

- The input described exactly: which rows and columns hold what, where the colour sits, what may and what may not be deleted, with cell addresses as Excel shows them. When the AI guessed at a web page, the HTML of the actual element copied from the page.
- After every run, what I saw rather than what I guessed ("only the uncoloured rows came together, the coloured ones are still mixed"), and the error message pasted as it was.
- The whole script asked for every time, not a fragment to splice in, so that nothing which already worked got lost on the way.
- Every version checked by eye against the source files, including the parts which had worked before.
- No guessing in the output: a status written only when the source states it, and a name left alone when nothing was read.

Each folder has the script, a fictional sample to run it on and a short account of the problems worth knowing about and how each was caught. The code is the last version I used, cleaned up for publication in October and November 2026: the paths, the client-specific settings and the comments, plus the fixes listed in each folder and marked in the code (3 in case 2, 3 in case 5, 3 in case 6).
