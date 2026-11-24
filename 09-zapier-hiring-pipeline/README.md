# 9. A hiring pipeline: from the shortlist to the decision, with Zapier and ClickUp (November 2026)

**The task.** At the law firm I also ran the first stages of hiring for the litigation practice: the job board, the test assignment, the answers, the recruiter's decision and the letters after it. Nothing connected these steps. The statuses lived in my memory and in flags in Outlook, I changed them by hand on the job board after reading the firm's mail, which the job board did not see, and every answer went to the recruiter as a forwarded letter with a changed subject and the resume attached by hand. Most candidates sent the answer right at the 96-hour deadline or a little late, about 1 in 10 sent extra files (the resume twice, a portfolio, versions in 2 languages), and about 1 in 3 forgot the resume when they were asked for it.

**What I built.** The same process, rebuilt in English for a fictional US firm, Hollis Grant LLP, as 1 system: the job board stays only for what cannot be automated (downloading resumes, a message in its chat), the candidate base and all the correspondence live in ClickUp and 4 Zaps, and the recruiter sees the whole base in ClickUp and decides by 1 word in a reply.

1. **The shortlist becomes a card and a test assignment.** The recruiter's only action is to save a resume from the job board into a Google Drive folder. A card appears in ClickUp, the candidate gets the assignment with a deadline in New York time, and the resume travels on to the recruiter later, so the candidate is never asked for it.
2. **The answer goes to the recruiter.** The candidate's reply is matched to the card by a tag in the subject, sorted by its attachments, and sent on to the recruiter with the answer, the resume and a link to the card.
3. **1 word decides.** The recruiter replies "invite", "decline" or "hold", typos allowed. The card moves, and the candidate gets the right letter.
4. **A report every Monday.** What waits for the recruiter, who has gone silent after the reminder, which questions wait for an answer, whom to contact through the job board.

Built on 23 - 24 November 2026 with Claude, which worked in the Zapier editor through the browser. My part was the process and its rules, which come from my own practice, and every test: each branch below was run on fictional candidates, and each problem in the table at the end was found by such a run.

## The rules, before the Zaps

| Situation | Rule |
| --- | --- |
| The deadline | 96 hours from sending, rounded up to the hour and moved into 10 AM - 7 PM on a weekday, New York time, and written in the letter in words |
| The answer file | 1 PDF named by a template, Answer_First_Last.pdf, so that it can be found among the signature images and the extra files |
| No email in the resume | The card gets the status "contact missing", and I get a task to ask for it in the job board chat |
| The same resume saved twice | No second card and no second letter |
| A question instead of an answer | A tag on the card and a task for me; the tag goes when the answer comes |
| No answer by the deadline | A reminder 3 hours after it, with the last date: 2 more days |
| No reaction to the reminder | After those 2 days the application is closed and the candidate gets a short letter |
| "hold" | A neutral letter now ("the review is in progress"), and after 10 days, if the card is still on hold, a letter about the waitlist |

## Zap 1: the shortlist becomes a card and a test assignment

| Step | What it does |
| --- | --- |
| Google Drive: new file in folder | A resume saved into "1 Shortlist" |
| Files by Zapier: text from file | The text of the PDF |
| Code by Zapier, Python | [1_read_resume.py](1_read_resume.py): the name, the email, the phone and the resume ID, the deadline, the reminder and the closing date in New York time, without any library for time zones |
| ClickUp: API request, then Filter | A search of the list by the resume ID: if a card already exists, the Zap stops here |
| ClickUp: create task, attach the resume | The card, with the deadline, the contacts and, in the description, the ID of the resume file |
| Google Drive: file by ID | The test assignment |
| Paths, 2 branches | A: an email exists. B: it does not, and I get a subtask |
| Path A | Gmail: the assignment. Delay until 3 hours after the deadline. If the status is still "test sent": the reminder, a tag, and the "contact confirmed" tag removed. Delay 2 more days. If there is still no answer and no new reply: status "rejected" and a closing letter |

## Zap 2: the answer goes to the recruiter

| Step | What it does |
| --- | --- |
| Gmail: new email matching search | A letter with "Test assignment" in the subject |
| Filter | Only a reply ("Re:"), only with the [ref] tag, and only one addressed to the firm, so that my own replies to candidates do not start the Zap |
| Code by Zapier, Python | [2a_find_card.py](2a_find_card.py): the card ID from the tag |
| ClickUp: find task, add the "contact confirmed" tag | |
| Code by Zapier, Python | [2b_sort_reply.py](2b_sort_reply.py): the answer by the template, copies of the resume, other documents, a note for the recruiter if the file was named otherwise or came as Word, and how late it came |
| Paths, 2 branches | A, a file came: the resume from Google Drive, the letter to the recruiter with both files, status "under review", the "question" tag removed. B, only text: a "question" tag and a subtask for me with the candidate's message |

## Zap 3: 1 word decides

| Step | What it does |
| --- | --- |
| Gmail: new email matching search | A reply from the recruiter to a "Review:" letter |
| Code, ClickUp: find task | The card, and its current status |
| Code by Zapier, Python | [3_read_decision.py](3_read_decision.py): the first line of the reply, without the quoted letter, compared with 14 signal words by edit distance (no typo allowed in words of 3 letters, 1 in words of up to 5, 2 in longer ones), the next status (an "invite" moves a candidate from the first interview to the second, and from the second to the offer) and the letter |
| Filter | An unclear reply changes nothing |
| ClickUp: status. Gmail: the letter | |
| Only for "hold" | Delay 10 days; if the card is still on hold, the waitlist letter |

## Zap 4: a report every Monday

| Step | What it does |
| --- | --- |
| Schedule | Monday, 9:00, New York time |
| ClickUp: API request | All the cards of the list |
| Code by Zapier, Python | [4_monday_report.py](4_monday_report.py): counts by status and 4 lists |
| Gmail: send email | The report to the recruiter |

The flags are tags, not custom fields: on the free plan of ClickUp, automations cannot change custom fields, so a tag is the only mark that Zapier and the recruiter's views can both use. The recruiter has 2 views in ClickUp: "Needs your decision", only the cards under review, the oldest first, and the board of the whole pipeline.

## Run the Python steps yourself

Each script runs outside Zapier (Python 3.7 or later, nothing to install): `python 4_monday_report.py` reads [sample/zap4_clickup_tasks.json](sample/zap4_clickup_tasks.json), 8 fictional cards and 1 subtask in the shape ClickUp returns them, and prints what Zapier would pass on:

```
Pipeline as of Tuesday, November 24: 8 candidates

  Contact missing    1
  Test sent          2
  Under review       2
  ...

Waiting for a decision (oldest first):
  - Maya Chen: 4 days with the recruiter
  - Daniel Ortiz: 1 day with the recruiter

Reminder sent after the deadline, still no answer:
  - Liam Novak
...
```

The dates in the scripts are counted from the moment of the run, as in Zapier, so the deadlines and the days in the output move with the calendar.

## Problems worth knowing about, and how each was caught

| Problem | How it showed | The fix |
| --- | --- | --- |
| The trial of Zapier ended | Zapier turned off every Zap with more than 2 steps, without moving them anywhere | The Zaps moved to a new account; before that, an export of all of them into 1 file, which is what made the move possible |
| The old Zaps were still running | A resume saved once gave 2 cards and 2 letters: the old account had not switched off its Zaps yet | All Zaps in the old account switched off by hand, and the extra card archived |
| The same resume twice | The test above, seen from the other side: nothing stopped a second card | The search by the resume ID before the card is created |
| The resume came as a login page | The letter to the recruiter carried a 400 KB HTML file named "login" instead of the resume: the link to an attachment in ClickUp works only for someone logged in | The ID of the resume file is written into the card, and the file comes from storage by that ID; a search by the file name did not find the file at all, so it was not an option |
| The mailbox was blocked | 2 letters to the recruiter stood in "Sent" and never arrived; then Microsoft blocked the whole account, storage included, and blocked its recovery too | The case moved from Outlook and OneDrive to Gmail and Google Drive. A personal mailbox is a poor sender for automatic letters; in the firm's own Microsoft 365 this would not happen |
| My own replies started the Zap | 1 question from a candidate gave 3 tasks: the Gmail trigger also sees sent letters, and my answer to the candidate looked like a new reply | The filter takes only letters addressed to the firm |
| The question stayed open | The "question" tag stayed on the card after the answer came, and the Monday report would have listed an answered question | The tag is removed when the answer comes |

2 of these I would point to. The blocked mailbox: the logic of the system was right, and it still failed, because of a part nobody looks at until it stops: the sender. It was caught because I checked the recipient's mailbox and did not stop at "sent". And my own replies: in the test everyone writes from 1 mailbox, so it looked like a quirk of the test, but in real work the coordinator answers candidates from the same mailbox the Zap watches, and every answer would have created a task.

## Prepared for publication

The firm, the candidates, their emails and the resume IDs are invented; the test letters went to aliases of my own mailbox. The scripts are the ones in the Zaps, plus the few lines which let them run outside Zapier with the sample files.
