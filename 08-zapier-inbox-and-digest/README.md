# 8. Inbox triage and a weekly digest, with Zapier (November 2026)

**The task.** My own job search: several dozen open applications at a time, kept in 1 Notion tracker, and the replies arriving in 1 Gmail mailbox, mixed with job alerts and other automatic letters. Each reply means a different next step: a rejection closes a line, a next step needs an answer the same day, a confirmation changes nothing but a date. And the most frequent outcome is no reply at all, which also needs a rule, or the tracker fills with lines which wait for nothing: an application without a reply in 10 days goes to "Silence".

**What I built.** 2 Zaps, both built by hand in the Zapier editor on 10 November 2026 and running on the real pipeline since then, plus a check by Claude on top of them:

1. **Replies sorted into Notion.** Gmail, a filter, a formatter and 3 paths: each reply becomes a record of its type in a Notion inbox, and the next-step letters also get a label in Gmail.
2. **A digest every Monday.** A schedule, a query to the tracker, a Python step ([weekly_digest.py](weekly_digest.py)) and 1 letter to myself: what is in progress, what has gone silent, what goes silent this week.
3. **The check.** Claude, connected to the same Zapier account through Zapier MCP, reads the inbox records not yet checked, compares them with the tracker and proposes the changes; it marks a record as checked, and nothing else: it never sends, archives or labels a letter, and never adds or deletes a line of the tracker unless I ask.

The point is 1 rule for every kind of letter, written down once, instead of a decision made again every morning on the phone.

## Zap 1: replies sorted into Notion

| Step | What it does |
| --- | --- |
| Gmail: new email matching search | A new letter in the mailbox which looks like a reply to an application |
| Filter | Job alerts stop here (subjects with "apply now" or "saved job"), so that nothing after it costs a task in Zapier |
| Formatter: date and time | The date of the letter converted from UTC to my time zone, UTC-5, before it reaches Notion |
| Paths, 3 branches | A: rejection. B: next step, and a label on the letter in Gmail, so that the mailbox and the tracker say the same. C: confirmation of an application |
| Notion: create item (in each path) | A record in the inbox database with the sender, the subject, the date and the type of the letter |

## Zap 2: the weekly digest

| Step | What it does |
| --- | --- |
| Schedule | Every Monday at 8:00 |
| Notion: query data source | All open lines of the tracker, with the filter in [notion_query_filter.json](notion_query_filter.json) |
| Code by Zapier, Python | [weekly_digest.py](weekly_digest.py): splits the lines into 3 blocks by status and by the days since the application |
| Gmail: send email | The digest to myself |

## Run the Python step yourself

`python weekly_digest.py` (Python 3.7 or later, nothing to install). Outside Zapier it reads [sample/zapier_input.json](sample/zapier_input.json), 15 fictional lines in the shape in which Zapier passes them (each field as 1 string with commas), as of Monday 16 November 2026, and prints [the letter](sample/digest_email.txt):

```
In progress - check whether anyone is waiting for you:
#101 Acme Demo Co
...
Time for Silence (10+ days):
#92 Umbrella Works - 13 days without a reply
...
Will become Silence this week:
#98 Wayne Staffing - Silence from 17.11
...
```

The line submitted the day before is left out on purpose: under 3 days it is not worth a mention yet.

## Problems worth knowing about, and how each was caught

| Problem | How it showed | The fix |
| --- | --- | --- |
| The filter looked at the body of the letter | A test on a job alert went through: the words sat in the subject | The filter moved to the subject |
| Zapier passes dates in UTC | The first records came into Notion with the wrong time of day | A Formatter step to UTC-5 before Notion |
| A path matched on the phrase "next steps" | A polite form letter from an agency ("about our next steps") would have been filed as a next step | The phrase removed; the path keys on phrases which only a real invitation uses |
| The wrong field mapped into the Python step | The step received an internal Notion property ID instead of dates, and every line was skipped | The date field picked again in the step's input |
| Silence counted from the wrong date | The tracker's date column held the day a vacancy was found, not the day of the application, and the first check moved 3 lines to "Silence" 2 days early | The 3 lines put back the same day; a separate "Submitted" column added and filled for 27 open lines, and the 10 days counted from it |

The last one is the one I would point to: the rule was right and the code was right, and the result was still wrong, because the data meant something else than its name. It was caught because I checked the first run against the dates I knew.

## Known limit

Zapier joins each field of the Notion results with commas, so a company name with a comma in it would shift the lines. None of mine have one; if it happens, the fix is to map the fields as line items instead of text.

## Prepared for publication

The companies, the numbers and the dates in the sample are invented. In my own tracker the statuses and the headings are in Russian; here they are in English, and that is the only change to the code, plus the local run with the sample file.
