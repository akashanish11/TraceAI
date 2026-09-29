# MediaService Incident

## System Overview

The MediaService processes application requests
through the write_file operation.

## Failure Behavior

During the incident, the service encountered
a condition associated with:

Disk full: no space left

The failure prevented the requested operation
from completing normally.

## Diagnostic Signal

The expected diagnostic signal for this incident is:

- Disk full: no space left
- StorageFullError
- No space left on device

## Relevant Component

- MediaService
- write_file
- write()

## Incident Category

Storage failure
