# ProductService Incident

## System Overview

The ProductService processes application requests
through the get_cached_value operation.

## Failure Behavior

During the incident, the service encountered
a condition associated with:

Cache connection failed

The failure prevented the requested operation
from completing normally.

## Diagnostic Signal

The expected diagnostic signal for this incident is:

- Cache connection failed
- CacheConnectionError
- Unable to connect to cache server

## Relevant Component

- ProductService
- get_cached_value
- get()

## Incident Category

Cache failure
