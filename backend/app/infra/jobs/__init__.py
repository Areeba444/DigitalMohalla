"""The scheduled jobs of ADR-0012, registered in the order a run executes them (plan items F4, F5).

Each job is small: `due()` is one SQL query for what is due at `now`, and `run()` does one item's
work through the unit of work (lifecycle store, notifier, case service). Timer values come from the
versioned config section `scheduler_b13`. Reminders run before the transitions they lead to, so a
single late run still reminds first.
"""

from app.domain.scheduler.runner import Job
from app.infra.jobs.lifecycle import (
    ConfirmationReminder,
    HandoverReminder,
    NoShow,
    OverdueEscalation,
    RequestExpiry,
    ReturnReminder,
)
from app.infra.jobs.other import InformationDeadline, ListingExpiry


def default_jobs() -> list[Job]:
    return [
        RequestExpiry(),
        HandoverReminder(),
        NoShow(),
        ReturnReminder(),
        OverdueEscalation(),
        ConfirmationReminder(),
        InformationDeadline(),
        ListingExpiry(),
    ]
