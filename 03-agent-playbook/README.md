# 3. A playbook which a person or an AI agent can follow

**Where it comes from.** At one of the firm's offsites a routine recheck, a week before departure, found that the carrier had moved 3 flights and told nobody: a car timed for the old schedule waits for a plane which is not there. It was resolved in 2 working days and nobody was lost, and afterwards I wrote it down as Playbook 2 of the offsite plan. In the model offsite of my portfolio it happens again: on 19 February the carrier moves OUT-2 from 22:40 to 23:30, and the departure transfer for 20 people stays where it was.

**What is new here.** The guidebook I wrote for my successor was meant for a person. [PLAYBOOK_2.md](PLAYBOOK_2.md) is written so that an AI agent connected to the workbook can follow it as well: the same steps, plus what the agent may and may not touch, and 2 checkpoints where it stops and waits for the coordinator. The agent finds the change, works out the new transfer within the buffer rules, lists the knock-on effects and drafts the messages; the decisions, and everything which leaves the team, stay with the coordinator.

**How to run it.** Make a copy of the [offsite control workbook](https://docs.google.com/spreadsheets/d/1VDJnpJWNu_MXEThhQAgW-Vc-XflvHn3kSKLHj5RXNk0/edit?usp=sharing) (File → Make a copy), connect an AI assistant with Google Sheets access to it, and give it PLAYBOOK_2.md with the line "Run this on [link to the copy]; the carrier's notice of 19 February says OUT-2 now departs at 23:30."

**What a correct run ends with.**

| | Before | After |
| --- | --- | --- |
| TR-D2, pick-up at the hotel | 19:00, buffer 270 minutes | 20:00, buffer 210 minutes (limits 150 - 240) |
| Flights, OUT-2, "Transfer updated" | No | Yes |
| Control, flight changes not carried into transfers | 1, red | 0, green |
| Control, transfers outside their buffer | 1, red | 0, green |
| Knock-on effects listed | | Late check-out until 18:00 (decision D3) leaves 2 hours to 20:00: luggage storage to agree with the hotel; museum programme for the late flight unchanged |
| Drafts | | 3 to the assistants (3, 11 and 6 names), 1 to the agency, 1 to the hotel |

## Run log

To be added after the first run: the agent's report, the 2 checkpoints and what I sent back.
