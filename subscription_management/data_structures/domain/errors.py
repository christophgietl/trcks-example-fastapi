import dataclasses


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Error:
    reason: str
