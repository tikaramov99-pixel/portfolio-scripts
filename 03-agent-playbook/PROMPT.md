Run the procedure below as an AI agent, on this Google Sheets workbook: PASTE THE LINK TO YOUR COPY HERE

I am the coordinator. Do not write anything in the workbook before I approve it in the way the procedure asks. Start with step 1, then send me your first question.

---

# Playbook 2: the carrier changed a flight time, and the change has not been carried through

Instructions for an AI agent connected to the offsite control workbook (Google Sheets). The same text is the procedure for a person; where the two differ, it says so.

## Why it is written this way

A flight change is found when everybody is busiest, and that is exactly when attention is lowest: a coordinator under pressure skims, answers "yes" to a block of text and misses the one line which mattered. The agent is there to cover that moment, the way an experienced assistant does: it does the reading and the arithmetic, brings 1 decision at a time in a form which takes 10 seconds to check, and does not move on without an answer which names what was decided.

## What you may and may not do

- Work only in the copy of the workbook named in the task, never in the original.
- Read any sheet. Write only the cells named in steps 4 and 7, and only after the approval asked for there.
- Do not send anything to anybody. You draft; the coordinator and the assistants send.
- Use names as they stand in the Participants sheet. Never copy passport data, phone numbers or allergies into a draft.
- If something does not match what this procedure expects, stop and report it instead of guessing.

## How to ask

Every time you need something from the coordinator, send 1 message with 1 question, built like this:

```
QUESTION 1 (of up to 4) · Confirm the new flight time

OUT-2, Sunday 21 March: the workbook says the carrier moved it from 22:40 to 23:30 (notice of 19 Feb).
Does the carrier's notice, or its website today, say 23:30?

Reply with:   23:30 confirmed
or with the time the carrier gives.
```

- The first line says which question it is and what it is about.
- Then only what is needed to decide: names, times and places, no cell addresses (those go in the report).
- Then the exact reply to copy, and what to write instead if the answer is no.
- Anything else you noticed goes after the question under "For information, no reply needed", never mixed into it.
- Accept only a reply which names what it approves. "Yes", "ok" or "I confirm" to anything but a single yes/no question approves nothing in particular: ask again, with the reply to copy.
- A draft with a gap in it (a placeholder, a missing time or place) is never shown for approval: ask for what is missing first.

The coordinator should be able to run the whole playbook by replying 4 times, each in 1 line.

## Steps

**1. Find what has not been carried through.**
On Flights, list every leg where "Changed" is Yes and "Transfer updated" is not Yes. For each, note the time as booked, the current time and the date of the change notice.

**2. Question 1: confirm the new time.**
Ask, as in the example above, whether the carrier's notice or its website today gives the time in "Dep, current" / "Arr, current". If the coordinator gives another time, stop: the workbook is wrong, not the transfer.

**3. Work out the new transfer.**
On Transfers, find the slot of that leg. Read the buffer limits on Lists (arrivals 30 - 75 minutes after landing, departures 150 - 240 minutes before take-off). Propose a new time inside the limits, rounded to 15 minutes, as close to the middle of the range as the programme allows (for a departure: take-off minus 195 minutes), and check that "Names assigned" still fits "Capacity".

**4. Question 2, checkpoint 1: approve the new pick-up time.**
Show 1 small table: slot, old time, new time, buffer before and after, people on it, seats. Reply to copy: "20:15 approved" (with the time you propose). Write nothing until then. After the approval, write the new time into the slot, set "Transfer updated" on Flights to Yes and replace the note on the slot with the date and what changed.

**5. Find the knock-on effects.**
At least: hotel check-out and luggage for the people on that leg (Rooming, and any open decision on Decisions which concerns them), the last programme item of that day (Programme), and the group transfer vendor. List each with what has to happen and who decides. This list is for information: it does not wait for a reply.

**6. Question 3, only if something is missing for the drafts.**
For example, the meeting point, if the slot's note does not give one. Ask for that 1 thing, with the reply to copy.

**7. Question 4, checkpoint 2: approve the drafts.**
Draft, complete and with nothing left open:
- 1 message per assistant with only the names of their people on that leg (from "Collected by"), the new pick-up time and the meeting point, for the assistant to forward;
- 1 message to the agency about the changed slot;
- 1 message to the hotel about check-out and luggage.
Show them numbered, each in its own block. Reply to copy: "Drafts 1 - 5 approved", or the numbers of the ones to change and what to change. After the approval, record on the slot's note that the messages were approved and when.

**8. Check the result and report.**
On Control, the indicators "Flight changes not yet carried into transfers" and "Transfers outside their time buffer or over capacity" should now be 0 for this leg. Report in this order:
1. What was found (step 1).
2. What was approved and written, cell by cell, before and after (step 4).
3. Knock-on effects and who owns each (step 5).
4. The drafts as approved (step 7).
5. Control before and after (step 8).
6. Anything you found wrong outside your write permissions.

## Changes after the first run (30 October 2026)

- 1 question per message, each with the reply to copy, and only an approval which names what it approves: in the first run "I confirm" was accepted as approval of 3 questions at once, and later of drafts with a gap in them.
- The departure rule now gives the number (take-off minus 195 minutes), since the README and the rule disagreed and the agent was right.
- Drafts take the meeting point from the slot's note, the departure slots now have one, and a missing detail is asked for before the drafts, not left as a placeholder in them.
