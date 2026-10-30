# Playbook 2: the carrier changed a flight time, and the change has not been carried through

Instructions for an AI agent connected to the offsite control workbook (Google Sheets). The same text is the procedure for a person; where the two differ, it says so.

## What you may and may not do

- Work only in the copy of the workbook named in the task, never in the original.
- Read any sheet. Write only the cells named in steps 4 and 6, and only after the approval asked for there.
- Do not send anything to anybody. You draft; the coordinator and the assistants send.
- Use names as they stand in the Participants sheet. Never copy passport data, phone numbers or allergies into a draft.
- If something does not match what this procedure expects, stop and report it instead of guessing.

## Steps

**1. Find what has not been carried through.**
On Flights, list every leg where "Changed" is Yes and "Transfer updated" is not Yes. For each, note the time as booked, the current time and the date of the change notice.

**2. Confirm the new time.**
Ask the coordinator for the carrier's notice or a fresh check on the carrier's site, and compare it with "Dep, current" / "Arr, current". If they differ, stop: the workbook is wrong, not the transfer.

**3. Work out the new transfer.**
On Transfers, find the slot of that leg. Read the buffer limits on Lists (arrivals 30 - 75 minutes after landing, departures 150 - 240 minutes before take-off). Propose a new time inside the limits, rounded to 15 minutes, as close to the middle of the range as the programme allows, and check that "Names assigned" still fits "Capacity".

**4. Checkpoint 1: the coordinator approves the new time.**
Show one table: slot, old time, new time, buffer before and after, names on it, capacity. Write nothing until the coordinator says yes. After the yes, write the new time into the slot, set "Transfer updated" on Flights to Yes and replace the note on the slot with the date and what changed.

**5. Find the knock-on effects.**
At least: hotel check-out and luggage for the people on that leg (Rooming, and any open decision on Decisions which concerns them), the last programme item of that day (Programme), and the group transfer vendor. List each with what has to happen and who decides.

**6. Checkpoint 2: the coordinator approves the drafts.**
Draft, for the coordinator to read before anything goes out:
- 1 message per assistant with only the names of their people on that leg (from "Collected by"), the new pick-up time and the meeting point, for the assistant to forward;
- 1 message to the agency about the changed slot;
- 1 message to the hotel about check-out and luggage.
After the yes, record on the slot's note that the messages were approved and when.

**7. Check the result.**
On Control, the indicators "Flight changes not yet carried into transfers" and "Transfers outside their time buffer or over capacity" should now be 0 for this leg. Report what you changed, cell by cell, and anything still open.

## Report format

1. What was found (step 1).
2. What was approved and written (step 4).
3. Knock-on effects and who owns each (step 5).
4. The drafts as approved (step 6).
5. Control before and after (step 7).
