# Offsite re-check: the rules

The offsite: Tbilisi, 4 days, 18 - 21 March 2027. 40 participants: 30 colleagues and 10 companions. The firm pays everything for the companions except their flights to Tbilisi and back. Today is Sunday 14 March 2027.

## The sources, and which one wins

- `participants.xlsx`: who takes part, the name as in the passport, colleague or companion, the room.
- `tickets/`: the e-tickets as received. **The ticket is the source of truth for flights and prices**, unless a carrier notice changes it.
- `airline_notices/`: schedule changes from the carrier. **A notice overrides the times on the tickets** for every passenger on that flight.
- `tickets_and_transfers.xlsx`: the table which 3 assistants filled in by hand. It is what is being checked; it is never the source of truth.
- `hotel_plan.xlsx`: what is booked with the hotel now, room by room.

The input files are never changed. Everything goes into new files.

## 1. Check the table against the tickets

For every participant: the name against the passport, the flights, the dates and times, and for colleagues the price. Report every difference, with the participant, the field, what the table says and what the ticket says. Also report a participant with no ticket, and a ticket with nobody on the list.

## 2. Transfers, airport to hotel and back

- Arrivals within **40 minutes** of the first arrival in the group share 1 vehicle. The same for departures.
- **1 - 4** people: a taxi. **5 - 16**: a minibus (Mercedes Sprinter type). **17 and more**: a bus.
- The plan comes out as a list of vehicles: date, time, flight(s), vehicle type, people.

## 3. The hotel

Standard check-in 14:00, check-out 12:00. A room's needs come from the earliest arrival and the latest departure of its guests:
- arrival before **11:00** on 18 March: early check-in;
- arrival before **06:00** on 18 March, or on 17 March: a full extra night from 17 March;
- departure after **15:00** on 21 March: late check-out.

Compare with the hotel plan and say, room by room, what has to be added and what has to be cancelled. Before any cancellation, look for a **transfer**: an early check-in, a late check-out or an extra night no longer needed in one room and needed in another is moved between the rooms, which is a request the hotel accepts far more easily than a cancellation plus a new booking. Only what is left after the transfers is a cancellation or an addition.

Free cancellation: up to **10% of all rooms** (here 3), until 3 days before check-in, that is, until 15 March. Say whether the cancellations fit.

## 4. Meals and activities

- Day 1, arrival before **14:00** (including those already there from 17 March): a lunch compensation in the budget, **GEL 45** per person.
- Day 1, the group leaves for Mtskheta at **16:00**: anybody arriving after that misses the dinner in Mtskheta. Give the dinner headcount.
- Day 4, the museum 15:00 - 17:30: only those flying at **20:30 or later** can come. Give the headcount, and the transfer rule applies to the trip to the museum as well.

## 5. Special cases go to the coordinator

Do not rebuild these automatically; list them for the coordinator with what was found:
- any route which does not start or end in Moscow, or which includes a train;
- a ticket reissued after the table was filled in, or any change nobody recorded;
- anything the rules above do not cover.

## The output

1. A report: what is wrong in the table, by participant.
2. The corrected plan: transfers, hotel changes (transfers between rooms, then additions and cancellations), lunch compensations, the Mtskheta dinner and the museum headcounts.
3. The list for the coordinator.

The whole check must run again with 1 command after every change in any of the files.
