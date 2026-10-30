# 3. A playbook which a person or an AI agent can follow

**Where it comes from.** At one of the firm's offsites a routine recheck, a week before departure, found that the carriers had moved 3 flights and told nobody: a car timed for the old schedule waits for a plane which is not there. It was resolved in 2 working days and nobody was lost, and afterwards I wrote it down as Playbook 2 of the offsite plan. In the model offsite of my portfolio it happens again: on 19 February the carrier moves OUT-2 from 22:40 to 23:30, and the departure transfer for 20 people stays where it was.

**What is new here.** The guidebook I wrote for my successor was meant for a person. [PLAYBOOK_2.md](PLAYBOOK_2.md) is written so that an AI agent connected to the workbook can follow it as well: the same steps, plus what the agent may and may not touch, and 2 checkpoints where it stops and waits for the coordinator. The agent finds the change, works out the new transfer within the buffer rules, lists the knock-on effects and drafts the messages; the decisions, and everything which leaves the team, stay with the coordinator.

**Why it is written this way.** A flight change is found when everybody is busiest, and that is exactly when attention is lowest: a coordinator, or a partner who has to approve something between 2 meetings, skims, answers "yes" to a block of text and misses the one line which mattered. So the agent asks 1 thing at a time, with the facts on 3 lines and the reply ready to copy, and does not move on without an answer which names what was decided. The whole run takes 4 one-line replies at most.

## Run it yourself in 5 minutes

1. **Make your own copy of the workbook.** Open the [offsite control workbook](https://docs.google.com/spreadsheets/d/1VDJnpJWNu_MXEThhQAgW-Vc-XflvHn3kSKLHj5RXNk0/edit?usp=sharing), then File → Make a copy. Keep the link to your copy.
2. **Open an AI assistant which can work in Google Sheets**, for example Claude with the Google Sheets connector switched on, signed in with the Google account which owns the copy.
3. **Give it the task.** Open [PROMPT.md](PROMPT.md), click "Copy raw file" (the icon at the top right of the file), paste it into a new chat, replace `PASTE THE LINK TO YOUR COPY HERE` with the link from step 1, and send.
4. **Answer its questions.** Each comes with the reply to copy. With the workbook as it is, expect 3:

| The agent asks | You reply |
| --- | --- |
| Is OUT-2 now at 23:30? | `23:30 confirmed` |
| Move the transfer TR-D2 from 19:00 to 20:15? | `20:15 approved` |
| Approve the 5 drafts (3 assistants, the agency, the hotel)? | `Drafts 1 - 5 approved` |

5. **Check the result** against the table and the screenshots below. Nothing has been sent to anybody: the drafts are in the chat, for you to send.

## What a correct run ends with

| | Before | After |
| --- | --- | --- |
| TR-D2, pick-up at the hotel | 19:00, buffer 270 minutes | 20:15, buffer 195 minutes (limits 150 - 240) |
| Flights, OUT-2, "Transfer updated" | No | Yes |
| Control, flight changes not carried into transfers | 1, red | 0, green |
| Control, transfers outside their buffer | 1, red | 0, green |
| Knock-on effects listed | | Luggage storage until 20:15 for the rooms on the late flight; late check-out until 18:00 still open as decision D3; museum programme unchanged |
| Drafts | | 3 to the assistants (3, 11 and 6 names), 1 to the agency, 1 to the hotel |

| Control before the run | Control after the run |
| --- | --- |
| ![Control before](images/control-before.png) | ![Control after](images/control-after.png) |

## Run log

**First run, 30 October 2026**, on a copy of the workbook, with Claude connected to Google Sheets; I acted as the coordinator.

| Step | What the agent did | What I did |
| --- | --- | --- |
| 1 - 2 | Found OUT-2 as the only leg changed and not carried through, and asked me to confirm 23:30 from the carrier's notice rather than taking the workbook's word for it | Answered at checkpoint 1 |
| 3 | Proposed 20:15 (195 minutes, the middle of the range) and pointed out that the expected result in this README, 20:00, did not follow the playbook's own rule | Agreed: the README was wrong, not the agent |
| Checkpoint 1 | Asked 3 questions at once: is 23:30 confirmed, 20:15 or 20:00, and where the meeting point is | Answered "I confirm", which the agent took as approval of all 3 |
| 4 | Wrote 3 cells, each named before and after | |
| 5 | Listed 6 knock-on effects, 2 of which I had not planned for: room R22, on the late flight, had no luggage arrangement at all, and the departure slot had no meeting point anywhere in the workbook | |
| Checkpoint 2 | Showed 5 drafts, the assistants' ones with "[meeting point]" left open | Answered "I confirm" again |
| 7 | Control: both red indicators green. Reported 2 things it was not allowed to fix: a stale "Next action" on Control and the README | |

**What the run taught, and what I changed.** The agent did its part as written; the weak point was the checkpoints, that is, me: "I confirm" approved a package of 3 questions, and later drafts which could not have gone out as they stood. The agent said so itself at the end of its report. So the playbook now asks 1 question at a time, accepts only an approval which names what it approves, and does not let a draft with a gap be approved at all; the departure slots in the workbook got a meeting point, the stale text on Control was corrected, and R22 went into the hotel request. The changes are listed at the end of [PLAYBOOK_2.md](PLAYBOOK_2.md).
