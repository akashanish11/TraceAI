# OrderService Incident

## System Overview

The OrderService processes application requests
through the publish_event operation.

## Failure Behavior

During the incident, the service encountered
a condition associated with:

Kafka message publish failed

The failure prevented the requested operation
from completing normally.

## Diagnostic Signal

The expected diagnostic signal for this incident is:

- Kafka message publish failed
- KafkaProducerError
- Failed to publish message

## Relevant Component

- OrderService
- publish_event
- send()

## Incident Category

Kafka failure
