# Rental Service: Race Condition Prevention Example

This document provides a concrete example of how PostgreSQL Exclusion Constraints prevent "Time-of-Check to Time-of-Use" (TOCTOU) race conditions in the Rental Service, specifically focusing on overlapping date ranges.

## The Scenario

Imagine we have a car (Car ID `123`) and two different workers trying to book it at the exact same time for slightly overlapping dates:
*   **Worker A** wants to book Car 123 from **June 1, 2027 to June 5, 2027**.
*   **Worker B** wants to book Car 123 from **June 3, 2027 to June 7, 2027**.

## The Problem (Without Exclusion Constraints)

If we rely on standard application-level logic:
1. Worker A checks the `rentals` table. The car is available for June 1-5.
2. Worker B checks the `rentals` table at the exact same microsecond. The car is available for June 3-7.
3. Both workers proceed to execute their `INSERT` statements simultaneously.
4. **Result:** Both rentals are saved, creating a double-booking overlap on June 3, 4, and 5.

## The PostgreSQL Solution

By implementing a **PostgreSQL Exclusion Constraint** on the `rentals` table, we instruct the database engine to mathematically reject overlapping date ranges (`&&` operator) for the same `car_id`. 

Here is what happens with the constraint in place:
1. Worker A and Worker B both check availability and see the dates are clear.
2. Both attempt to `INSERT` their records.
3. PostgreSQL processes Worker A's request first and successfully saves the rental (June 1-5).
4. A microsecond later, PostgreSQL attempts to process Worker B's insert (June 3-7). 
5. The database engine calculates that Worker B's dates overlap with Worker A's new row.
6. **Result:** PostgreSQL forcefully blocks Worker B's insert and throws an `IntegrityError`. 

The Exclusion Constraint automatically handles any type of overlap:
*   **Partial overlap** (e.g., June 1-5 and June 3-7) ➡️ **Rejected!**
*   **Exact match** (e.g., June 1-5 and June 1-5) ➡️ **Rejected!**
*   **Fully inside** (e.g., June 1-10 and June 3-4) ➡️ **Rejected!**

This guarantees that a car can never be double-booked for even a single overlapping day, regardless of how many concurrent workers the Rental Service runs.

## Why the Pre-Check and Atomic Reserve MUST be Separate

In the Rental Service flow, there are two distinct steps before inserting a rental:
1. **Pre-check**: The service queries its own `rentals` table to check there is no other rental for this car in this time period.
2. **Atomic Reserve**: The service makes a synchronous API call to the Vehicle Service to verify availability and update the status to "In use".

You might wonder: *Why can't these two steps be united into a single database query?*

The answer lies in the strict rule of our **Microservices Architecture**: **"NO Direct DB Access."**
* The **Pre-check** requires reading the `rentals` table, which is privately owned by the **Rental Service**.
* The **Atomic Reserve** requires updating the `cars` table, which is privately owned by the **Vehicle Service**.

Because these two tables live in physically isolated environments (two different microservices, each with their own database access), it is impossible to run a single unified SQL query (like a `JOIN`) that touches both. 

The Rental Service must first execute a local query against its own database (the Pre-check), and if successful, it must make an orchestrated network HTTP request to the Vehicle Service to trigger the update there (the Atomic Reserve). This separation is the fundamental trade-off of microservices: you gain independent scalability, but operations spanning multiple domains must be orchestrated in separate steps over the network.
