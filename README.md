# Working with AI: 2 scripts from January 2026, and 2 cases from October

Two real tasks from my work in the operations of a law firm in Moscow, January 2026, which I solved with Python scripts written by ChatGPT to my specification. I do not write code myself: my part was to describe the task and the files precisely enough, to run every version on the real files and to say exactly what came out wrong, until the result did what the task needed.

Both scripts are simple by today's standards. In January 2026, though, AI worked in a chat window and could not see my files or run anything: every version travelled from the chat to my computer and back, and the real work was in the checking.

Cases 3 and 4 are from October 2026 and show where this has gone since: one of my offsite procedures rewritten so that an AI agent working inside the workbook can follow it, under checkpoints; and the other end of the scale: a monthly check of a confidential file done entirely on 1 computer, with no internet and no AI involved at all, for the cases where nothing may leave the office even in theory.

All data in the samples is fictional. The real files were confidential and are not published; the scripts processed them on my own machine.

| Case | The task | Result |
| --- | --- | --- |
| [1. Rows grouped by colour](01-group-rows-by-highlight/) (January 2026) | Monthly time entries for the firm's key client: put together the rows of a Word table which are marked with the same colour | 1 script, used for the monthly report |
| [2. Ledger clean-up](02-ledger-cleanup/) (January 2026) | Folders of quarterly VAT ledger exports: delete the empty columns, rebuild the header, add the total, fit the print, then 1 summary table per folder | 2 scripts, used on 2 folders |
| [3. A playbook for a person or an AI agent](03-agent-playbook/) (October 2026) | The offsite playbook for a flight moved by the carrier, rewritten so that an AI agent connected to the workbook can follow it, stopping for the coordinator's approval | The playbook, 2 logged runs, and a 5-minute guide to run it yourself |
| [4. Confidential data, checked entirely on 1 computer](04-offline-analysis/) (October 2026) | A month of lawyers' time entries checked before billing: duplicates, days over 10 hours, empty descriptions, wrong rates, matters over their cap | A program in 1 file which needs nothing but Python, switches off its own network access and only reads the file |

## How I worked with the AI

- The input described exactly: which rows and columns hold what, where the colour sits, what may and what may not be deleted, with cell addresses as Excel shows them.
- After every run, what I saw rather than what I guessed ("only the uncoloured rows came together, the coloured ones are still mixed"), and the error message pasted as it was.
- The whole script asked for every time, not a fragment to splice in, so that nothing which already worked got lost on the way.
- Every version checked by eye against the source files, including the parts which had worked before.

Each folder has the script, a fictional sample to run it on and a short account of the problems worth knowing about and how each was caught. The code is the last version I used, cleaned up for publication in October 2026: the paths, the client-specific settings and the comments, plus 3 fixes in 1 script which are listed and marked in the code.
