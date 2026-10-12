"""Named refusals of the lifecycle. Raised by the event store and the service; mapped to HTTP codes
at the API edge (Architecture_Design.md section 4: 403 not allowed, 404, 409 invalid/stale/taken)."""


class EventStoreError(Exception):
    """Base class for refusals from the event store."""


class StaleCommand(EventStoreError):
    """The command was based on an older version of the stream (optimistic concurrency)."""


class InvalidTransition(EventStoreError):
    """The move is not in the transition table, or a transition guard failed."""


class NotAuthorised(EventStoreError):
    """The actor may not make this move."""


class DatesTaken(EventStoreError):
    """The booking calendar refused the dates (exclusion constraint, ADR-0002)."""


class StreamNotFound(EventStoreError):
    """No transaction with this id."""
