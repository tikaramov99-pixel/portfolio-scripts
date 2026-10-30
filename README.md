# Working with AI: 2 scripts from January 2026 and an agent playbook from October

Two real tasks from my work in the operations of a law firm in Moscow, January 2026, which I solved with Python scripts written by ChatGPT to my specification. I do not write code myself: my part was to describe the task and the files precisely enough, to run every version on the real files and to say what exactly came out wrong, including the cases where the AI reported a fix which in fact had not happened, until the result did what the task needed.

Both scripts are simple by today's standards. In January 2026, though, I worked with AI in a chat window, and every version travelled from the chat to my computer and back: 9 rounds for the first task and 40 for the second, most of them spent catching what the AI reported as fixed and was not.

Case 3 is from October 2026 and is of another kind: not a script, but one of my offsite procedures rewritten so that an AI agent working inside the workbook can follow it, under 2 checkpoints, with the log of its first run and what I changed after it.

All data in the samples is fictional. The real files were confidential and are not published; the scripts processed them on my own machine.

| Case | The task | Rounds | Result |
| --- | --- | --- | --- |
| [1. Rows grouped by colour](01-group-rows-by-highlight/) | Monthly time entries for the firm's key client: put together the rows of a Word table which are marked with the same colour | 9 | 1 script, used for the monthly report |
| [2. Ledger clean-up](02-ledger-cleanup/) | Folders of quarterly VAT ledger exports: delete the empty columns, rebuild the header, add the total, fit the print, then 1 summary table per folder | 40 | 2 scripts, used on 2 folders |
| [3. A playbook for a person or an AI agent](03-agent-playbook/) (October 2026) | The offsite playbook for a flight moved by the carrier, rewritten so that an AI agent connected to the workbook can follow it, with 2 checkpoints where it waits for the coordinator | 1 run, logged | The playbook, tightened after the run |

## How I worked with the AI

- The input described exactly: which rows and columns hold what, where the colour sits, what may and what may not be deleted, with cell addresses as Excel shows them.
- After every run, what I saw rather than what I guessed ("only the uncoloured rows came together, the coloured ones are still mixed"), and the error message pasted as it was.
- The whole script asked for every time, not a fragment to splice in, so that nothing which already worked got lost between rounds.
- Every version checked by eye against the source files; most of the rounds in the logs below are what this check caught.

Each folder has the script, a fictional sample to run it on and a log of the rounds. The code is the last version I used, cleaned up for publication in October 2026 with Claude: the paths, the client-specific settings and the comments, plus 3 fixes in 1 script which are listed and marked in the code.
