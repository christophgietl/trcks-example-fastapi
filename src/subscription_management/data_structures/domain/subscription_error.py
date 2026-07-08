import dataclasses
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from uuid import UUID


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class _SubscriptionErrorWithId:
    id: UUID


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class SubscriptionWithIdAlreadyExistsError(_SubscriptionErrorWithId):
    pass


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class SubscriptionWithIdDoesNotExistError(_SubscriptionErrorWithId):
    pass
