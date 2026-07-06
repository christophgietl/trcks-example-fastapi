from uuid import uuid7

from subscription_management.data_structures.domain.subscription import (
    SubscriptionDoesNotExistError,
    SubscriptionError,
    SubscriptionIdAlreadyExistsError,
)


def test_subscription_does_not_exist_error_defaults() -> None:
    error = SubscriptionDoesNotExistError()
    assert error.reason == "Subscription does not exist"
    assert error.id is None


def test_subscription_does_not_exist_error_with_id() -> None:
    subscription_id = uuid7()
    error = SubscriptionDoesNotExistError(id=subscription_id)
    assert error.reason == "Subscription does not exist"
    assert error.id == subscription_id


def test_subscription_error_stores_reason() -> None:
    error = SubscriptionError(reason="Subscription does not exist")
    assert error.reason == "Subscription does not exist"


def test_subscription_id_already_exists_error() -> None:
    subscription_id = uuid7()
    error = SubscriptionIdAlreadyExistsError(id=subscription_id)
    assert error.reason == "ID already exists"
    assert error.id == subscription_id
