# CatalogService Incident

## System Overview

The CatalogService processes application requests
through the call_dependency operation.

## Failure Behavior

During the incident, the service encountered
a condition associated with:

Request timeout after 3000ms

The failure prevented the requested operation
from completing normally.

## Diagnostic Signal

The expected diagnostic signal for this incident is:

- Request timeout after 3000ms
- RequestTimeoutError
- Request timeout after 3000ms

## Relevant Component

- CatalogService
- call_dependency
- request()

## Incident Category

API request timeout
