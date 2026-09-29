# Order Service Inventory API Timeout

## System Overview

The OrderService calls InventoryService to retrieve
inventory information before completing an order.

## API Request Behavior

The HTTP client waits for a response from InventoryService.

The configured request timeout is 3000 milliseconds.

## Failure Behavior

If InventoryService does not respond within the
configured timeout:

1. The HTTP client raises RequestTimeoutError.
2. OrderService marks the inventory request as failed.
3. The order cannot be completed.
4. A failure response is returned to the client.

## Expected Diagnostic Signal

An API request timeout typically produces:

- Request timeout
- RequestTimeoutError
- Inventory request failed
- Unable to complete order

## Relevant Components

- OrderService
- InventoryService
- HttpClient
- inventory_client.get_inventory()