# RecommendationService Incident

## System Overview

The RecommendationService processes application requests
through the generate operation.

## Failure Behavior

During the incident, the service encountered
a condition associated with:

Java heap space exhausted

The failure prevented the requested operation
from completing normally.

## Diagnostic Signal

The expected diagnostic signal for this incident is:

- Java heap space exhausted
- java.lang.OutOfMemoryError
- Java heap space

## Relevant Component

- RecommendationService
- generate
- buildMatrix()

## Incident Category

Memory exhaustion
