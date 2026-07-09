from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from decimal import Decimal
    from uuid import UUID

    from subscription_management.data_structures.domain.product import ProductStatus

type ProductTuple = tuple[UUID, Decimal, str, ProductStatus]
type StrDict = dict[str, object]
type SubscriptionTuple = tuple[UUID, bool, UUID, UUID]
type UserTuple = tuple[UUID, str]


def _get_id(d: StrDict) -> str:
    return str(d["id"])


def _sorted_by_id(ds: Iterable[StrDict]) -> list[StrDict]:
    return sorted(ds, key=_get_id)


def _to_product_dict(product: ProductTuple) -> StrDict:
    return {
        "id": str(product[0]),
        "monthly_fee_in_euros": str(product[1]),
        "name": product[2],
        "status": product[3],
    }


def _to_subscription_dict(
    subscription: SubscriptionTuple, product: ProductTuple
) -> StrDict:
    return {
        "id": str(subscription[0]),
        "is_active": subscription[1],
        "product": _to_product_dict(product),
    }


def _to_user_dict(
    user: UserTuple, subscriptions: Iterable[tuple[SubscriptionTuple, ProductTuple]]
) -> StrDict:
    return {
        "id": str(user[0]),
        "email": user[1],
        "subscriptions": [
            _to_subscription_dict(subscription, product)
            for subscription, product in subscriptions
        ],
    }


@pytest.fixture
def sorted_by_id() -> Callable[[Iterable[StrDict]], list[StrDict]]:
    return _sorted_by_id


@pytest.fixture
def to_product_dict() -> Callable[[ProductTuple], StrDict]:
    return _to_product_dict


@pytest.fixture
def to_subscription_dict() -> Callable[[SubscriptionTuple, ProductTuple], StrDict]:
    return _to_subscription_dict


@pytest.fixture
def to_user_dict() -> Callable[
    [UserTuple, Iterable[tuple[SubscriptionTuple, ProductTuple]]], StrDict
]:
    return _to_user_dict
