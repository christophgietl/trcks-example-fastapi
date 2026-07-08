import dataclasses
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from uuid import UUID


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class _UserErrorWithEmail:
    email: str


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class _UserErrorWithId:
    id: UUID


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class UserWithEmailAlreadyExistsError(_UserErrorWithEmail):
    pass


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class UserWithEmailDoesNotExistError(_UserErrorWithEmail):
    pass


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class UserWithIdAlreadyExistsError(_UserErrorWithId):
    pass


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class UserWithIdDoesNotExistError(_UserErrorWithId):
    pass
