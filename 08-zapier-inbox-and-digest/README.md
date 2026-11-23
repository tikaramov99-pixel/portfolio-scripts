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
| Notion: query data source | All open lines of the tracker, with the filter in [notion_query_filter.json](notion_query_filter.json); each line comes already joined into 1 string by a formula property ([notion_formula.txt](notion_formula.txt)) |
| Code by Zapier, Python | [weekly_digest.py](weekly_digest.py): splits the lines into 3 blocks by status and by the days since the application, and lists separately any line it could not read |
| Gmail: send email | The digest to myself |

## Run the Python step yourself

`python weekly_digest.py` (Python 3.7 or later, nothing to install). Outside Zapier it reads [sample/zapier_input.json](sample/zapier_input.json), 15 fictional lines in the shape in which Zapier passes them (1 field, the lines separated by commas, the fields of a line by "|"; 1 company has a comma in its name, as in real life), as of Monday 16 November 2026, and prints [the letter](sample/digest_email.txt):

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
| Companies attached to the wrong numbers (found 23 November 2026) | The step received 4 separate lists (numbers, companies, statuses, dates) and paired them by position. 2 company names in the tracker had a comma inside, Zapier's own separator, so from that line on every company moved to someone else's number: the digest put one company's name next to another company's number. The dates were not affected, so the Silence rule kept working, which is why it went unnoticed for about a week | A formula property in Notion joins each line into 1 string (number, company, status, date; commas in names become ";"), the step receives that 1 field, and any line it cannot read goes to a separate block of the letter instead of being paired with the wrong data |

2 of these I would point to. The date one: the rule was right and the code was right, and the result was still wrong, because the data meant something else than its name; it was caught because I checked the first run against the dates I knew. And the comma one: I had written it down here as a known limit with "none of mine have one", and within a week 2 of mine had one. It was caught the same way, by reading the digest against the tracker, not by trusting it. The fix removes the cause rather than the symptom: 1 line travels as 1 piece, so nothing can drift apart.

## Prepared for publication

The companies, the numbers and the dates in the sample are invented. In my own tracker the statuses and the headings are in Russian; here they are in English, and that is the only change to the code, plus the local run with the sample file.
