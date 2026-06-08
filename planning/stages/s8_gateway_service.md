# Stage 8: Main Service / API Gateway - Deep Dive

This document provides a detailed exploration of **Stage 8** from the `project_implementation_plan.md`. It explains the architecture and responsibilities of the Main Service, which acts as the API Gateway for the entire DriveNow system.

## Overview
In a microservices architecture, exposing multiple different services directly to clients (like mobile apps or front-end websites) creates chaos. Clients would have to manage multiple IP addresses, ports, and handle CORS complexities. The API Gateway solves this by serving as the unified "Single Entry Point" or "Front Door" to the entire system.

---

## 1. The Single Entry Point Concept

From the perspective of an external client, the DriveNow system appears to be a traditional monolith running on a single URL (e.g., `http://localhost:8000`). The client is completely unaware that behind the scenes, their requests are being handled by different isolated containers.

The Gateway provides a single, cohesive OpenAPI (Swagger) documentation page that combines all available actions across the system.

---

## 2. Synchronous HTTP Proxying (`httpx`)

The core function of the Gateway is routing traffic. It achieves this using **Synchronous HTTP Proxying**.

* **The Mechanism:** When a client sends a request to the Gateway, the Gateway uses the asynchronous `httpx` client to immediately forward that request to the appropriate internal microservice over the internal Docker network (`drivenow_net`).
* **Routing Logic:**
  * Requests directed to `/cars/*` are proxied synchronously to the **Vehicle Service**.
  * Requests directed to `/rentals/*` are proxied synchronously to the **Rental Service**.
  * Requests directed to `/returns/*` are proxied synchronously to the **Return Service**.
* **Waiting for Response:** Because the proxying is synchronous, the Gateway keeps the client's connection open, waits for the downstream service to reply, and then relays that exact response back to the client.

---

## 3. Strict Requirement: Absolute Statelessness

A critical architectural rule defined in Stage 8 is that the Gateway **must NOT hold a database.**

* **Why?** The Gateway's only job is to route traffic and measure performance. It does not own any domain data.
* **Benefits:** This makes the Gateway absolutely stateless. It requires almost zero memory footprint, and if the container crashes or if traffic spikes exponentially, the Gateway can be scaled horizontally (spinning up 5 or 10 identical Gateway instances behind a load balancer) instantly, with zero concerns about database replication or locking.

---

## 4. Centralized Observability via Middleware

Because 100% of external traffic passes through the Gateway, it is the most strategic location to measure the overall health and speed of the system.

* **Prometheus Metrics via Middleware:** The Gateway implements a FastAPI Middleware function. This function intercepts every incoming HTTP request, starts a timer, proxies the request, and stops the timer when the response returns. 
  * It then pushes this data to Prometheus, strictly fulfilling the requirement to track the **`Average response time`** of all synchronous requests passing through the system.
* **Structured Logging:** Following the Stage 2 rules, the Gateway utilizes the standard Python `logging` module to output structured logs to both `stdout` (for Docker aggregation) and a physical `app.log` file.
  * *Example Trace:* `[GatewayService] 2026-06-08 19:30:00 - INFO - Proxied GET /cars to Vehicle Service in 42ms.`
