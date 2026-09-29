# Payment Service Database Connection Pool

## System Overview

The PaymentService uses a shared database connection pool to process
customer payment transactions.

The connection pool has a maximum capacity of 20 active connections.

## Connection Acquisition

Before processing a payment, PaymentService requests a connection
from DatabasePool.

If all 20 connections are already active, a new request cannot acquire
a connection until an existing connection is released.

## Failure Behavior

When no database connection is available:

1. PaymentService waits for a connection.
2. The request times out after 3000 milliseconds.
3. The payment transaction fails.
4. PaymentService retries the request.

## Known Risk

Long-running database queries or connections that are not released
properly can exhaust the connection pool.

## Relevant Components

- PaymentService
- DatabasePool
- process_payment()
- database_pool.acquire()

## Expected Diagnostic Signal

A connection pool exhaustion incident typically produces:

- "Connection pool exhausted"
- "Unable to acquire database connection"
- "Connection timeout"
- Payment transaction failures