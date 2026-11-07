"""Statistics from the event log of the Drooff fire+ (php/easevents.php)."""

from __future__ import annotations

from dataclasses import asdict, dataclass

# Door values in the event log: "auf" open, "zu" closed, "azu" opened and closed between two
# entries (the web app always draws it as a door event)
DOOR_OPENED = ("auf", "azu")
PHASE_HEATING = "Anheizen"
PHASE_REGULAR = "Regeln"

# Door openings closer than this count as one reload (s); with a fire+ reloads are 30 min or more apart
RELOAD_GAP = 600


@dataclass(frozen=True)
class FireplusEvent:
    """One entry of the event log: time (Unix seconds, UTC), door and phase."""

    time: int
    door: str
    phase: str


def parse_events(response: str) -> list[FireplusEvent]:
    """Parse the response of easevents.php: '"time,door,phase,time,door,phase,"'."""
    values = response.lstrip("\ufeff").strip().strip('"').split(",")
    events = []
    for index in range(0, len(values) - 2, 3):
        time, door, phase = values[index : index + 3]
        if time.strip().isdigit():
            events.append(FireplusEvent(int(time), door.strip(), phase.strip()))
    return events


@dataclass
class FireplusStatistics:
    """Counters derived from the event log, stored across restarts."""

    last_event: int = 0
    reloads: int = 0
    fires: int = 0
    wood: float = 0.0
    last_reload: int | None = None
    last_opened: int | None = None
    phase: str | None = None
    # last recommended wood load above 0 (kg), used while the fire+ reports none (for example in standby)
    wood_load: float | None = None
    # fires and reloads counted while no wood load was known yet, booked once one is reported
    wood_pending: int = 0

    @classmethod
    def from_dict(cls, data: dict | None) -> FireplusStatistics:
        """Restore stored statistics."""
        fields = cls.__dataclass_fields__
        return cls(**{key: value for key, value in (data or {}).items() if key in fields})

    def as_dict(self) -> dict:
        """Return the statistics for storing."""
        return asdict(self)

    def process(self, events: list[FireplusEvent], wood_load: float | None) -> bool:
        """
        Count fires and reloads in new events, return whether anything changed.

        A fire starts when the phase changes from heating up to regular operation. A reload is
        a door opening during regular operation; openings within RELOAD_GAP count once. The
        wood is estimated: the recommended wood load of the fire+ for every fire and reload. The
        load is the current one; while the fire+ reports none, the last known one is used.
        """
        changed = False
        if wood_load and wood_load > 0:
            self.wood_load = wood_load
            if self.wood_pending:
                self.wood += self.wood_pending * wood_load
                self.wood_pending = 0
                changed = True
        for event in sorted(events, key=lambda event: event.time):
            if event.time <= self.last_event:
                continue
            if event.phase == PHASE_REGULAR and self.phase == PHASE_HEATING:
                self.fires += 1
                self._add_wood()
            if event.phase == PHASE_REGULAR and event.door in DOOR_OPENED:
                if self.last_opened is None or event.time - self.last_opened > RELOAD_GAP:
                    self.reloads += 1
                    self._add_wood()
                    self.last_reload = event.time
                self.last_opened = event.time
            self.phase = event.phase
            self.last_event = event.time
            changed = True
        self.wood = round(self.wood, 2)
        return changed

    def _add_wood(self) -> None:
        if self.wood_load:
            self.wood += self.wood_load
        else:
            self.wood_pending += 1
