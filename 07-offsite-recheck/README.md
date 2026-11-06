# 7. An offsite plan re-checked after every change, with Claude Code (November 2026)

**The task.** An offsite for about 40 people: 30 colleagues and 10 companions, whom the firm hosted in full except for their flights. The tickets were bought, and the data collected, by 3 assistants, each into the same shared table, and every change after that had to travel through the same table: a carrier moving a flight, a participant changing a ticket himself and telling only one of the assistants, a hearing set in another city on the eve of Day 1. On a real offsite I found such a change only because 2 flights had been moved by the airlines and I re-checked the flight times of every passenger. And every change moves more than the flight: who shares which car from the airport, which room needs an early check-in or a late check-out, who gets a lunch compensation on Day 1 and who misses the dinner, how many come to the museum on the last day.

**What the script does.** It takes the e-tickets, the carrier's notices, the participant list and the hotel plan as the truth, checks the assistants' table against them, and rebuilds the plan from my rules in [rules.md](rules.md): arrivals within 40 minutes share a car (up to 4 a taxi, 5 - 16 a minibus, more a bus); early check-in, late check-out and extra nights by flight times, moved between rooms before anything is cancelled, since a hotel accepts a swap far more easily than a cancellation, and with the free-cancellation limit of 10% of the rooms checked; lunch compensations, the dinner and the museum counted again. What the rules do not cover goes to the coordinator, with the assistant responsible for each case. The point is 1 channel which re-checks the whole plan after every change with 1 command, so that nobody has to re-check anybody's work by hand.

**Who did what.** The rules are mine, from the offsites I ran, written down for this case. The fictional sample was prepared with Claude in a chat, with the problems I had met on real offsites built into it. The script was written and run by Claude Code on my own computer; my part was the task, the answers to its questions, the corrections, and checking its result against the cases I knew were in the sample.

**How this differs from [case 4](../04-offline-analysis/).** Case 4 is also a check which produces a report, and it is there to show something else: a small finished application for people who will never open a terminal, built with Claude in a chat window, where every version travelled to my computer and back by hand. This case shows the work in Claude Code, where the AI reads the files, runs the script and sees its own errors, and my part moves to setting the rules and checking.

## Run it yourself

1. `pip install openpyxl pypdf python-docx`
2. `python offsite_check.py`. It reads the fictional sample in `sample/`: 40 participants, 39 e-tickets (1 is missing on purpose), 2 carrier notices, the assistants' table and the hotel plan, as of 14 March 2027, 4 days before Day 1.
3. A short report appears in the window, and 2 files in `sample/output/`, numbered and dated so that no run overwrites an earlier one: an Excel workbook with the table errors, the corrected plan and the coordinator's list, and a 1-page Word summary to send to a manager.

`python offsite_check.py <folder>` runs it on any folder with the same files; `python make_sample.py` makes the sample again.

What appears in the window on the sample:

```
OFFSITE CHECK  Tbilisi 18.03-21.03.2027  (today 14.03.2027)
Table errors: 41 differences in 21 participants
Indicator                      Assistants table                ->  Tickets + notices
Arrival transfers              5 (3 taxi, 1 minibus, 1 bus)    ->  7 (5 taxi, 1 minibus, 1 bus)
Departure transfers            3 (1 taxi, 1 minibus, 1 bus)    ->  3 (1 taxi, 1 minibus, 1 bus)
Mtskheta dinner, people        26                              ->  26
Museum, people / vehicle       23 / bus                        ->  24 / bus
Lunch compensation             26 / GEL 1170                   ->  8 / GEL 360
Hotel: room-to-room transfers  2                               ->  2
Hotel: additions               1                               ->  1
Hotel: cancellations           0 (fits free limit 3)           ->  0 (fits free limit 3)
SPECIAL CASES (6)
- P15 BOGDANOV [assistant B]: route Krasnodar > Sochi > Yerevan > Tbilisi > Moscow incl. train
- P18 SMIRNOVA [assistant B]: ticket name SMIRNOVA/MARIIA != passport
- P22 ROMANOVA [assistant B]: ticket reissued 05.03.2027: out NR 218 23:30
- P27 ILYIN [assistant C]: no ticket; planned UNCONFIRMED as NR 215 20:50 / NR 218 23:30
- Carrier: NR 211 18.03 now 10:20-14:35 (18 pax, not in table)
- Carrier: NR 216 21.03 now 11:10-13:30 (15 pax, not in table)
```

(Shortened: each case also has its next action, and the 2 schedule changes list the passengers by the assistant who has to tell them.) The lunch line is the one a manager reads first: the table would have budgeted GEL 1,170 for 26 people, because nobody had entered the moved flight, which now lands after 14:00.

## How it was built

5 rounds on 6 November 2026, the first 4 in Claude Code.

| Round | What happened | My part |
| --- | --- | --- |
| 1 | Claude Code read the rules and all the files, then asked 3 questions before writing anything: what to do with the hotel rooms of the special cases, which language the report should be in, and what time a car to the airport should leave | My answers: the rooms of special cases are not changed automatically, only shown to the coordinator; English; a fixed time before the flight, which Claude Code set at 3 hours. The first run found every problem built into the sample, and the counts matched the answer key prepared with it |
| 2 | The participant without a ticket had been left out of everything: no car, no museum, no bus to the airport | My rule: plan him from the table, marked unconfirmed, and keep him on the coordinator's list. A spare seat in a minibus costs less than a person at the airport with no car |
| 3 | The results were only in Excel | A short report in the window, as the table had it against as the tickets have it, then the special cases with the next action for each; in English, since the Windows console broke the Cyrillic |
| 4 | Nothing ready to send upwards | A Word summary for a manager, the main point first and then the numbers, with the responsible assistant for every case and the passengers of each moved flight grouped by the assistant who has to tell them |
| 5 | Each run overwrote the last report | Reports numbered and dated, with the number and the time inside each file too. This last change was made with Claude in a chat rather than in Claude Code |

## Prepared for publication

The participants, the flights, the carrier and the prices are invented; the firm and the real offsite are not named. The script is the one Claude Code wrote, with round 5 and 1 publication change: run without a folder, it uses `sample/` when the input files are not beside it.
