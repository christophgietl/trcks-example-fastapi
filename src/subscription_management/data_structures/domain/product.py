import dataclasses
from typing import TYPE_CHECKING, Literal, final

if TYPE_CHECKING:
    from decimal import Decimal
    from uuid import UUID

    from subscription_management.data_structures.domain.do_not_update import (
        DO_NOT_UPDATE,
    )

type ProductStatus = Literal["draft", "published", "deprecated"]


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class _Product:
    id: UUID
    monthly_fee_in_euros: Decimal | DO_NOT_UPDATE
    name: str | DO_NOT_UPDATE
    status: ProductStatus | DO_NOT_UPDATE


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Product(_Product):
    monthly_fee_in_euros: Decimal
    name: str
    status: ProductStatus


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductUpdate(_Product):
    pass
