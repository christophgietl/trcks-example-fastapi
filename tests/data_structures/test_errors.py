from dataclasses import FrozenInstanceError
from uuid import uuid7

import pytest

from subscription_management.data_structures.domain.errors import (
    Error,
    ProductDoesNotExistError,
    ProductError,
    ProductIdAlreadyExistsError,
    ProductInDeprecatedStatusError,
    ProductInDraftStatusError,
    ProductNameAlreadyExistsError,
    ProductPayloadUpdateError,
    ProductStatusDeprecatedError,
    ProductStatusPublishedError,
    ProductStatusUpdateError,
    SubscriptionDoesNotExistError,
    SubscriptionError,
    SubscriptionIdAlreadyExistsError,
    UserDoesNotExistError,
    UserEmailAlreadyExistsError,
    UserError,
    UserIdAlreadyExistsError,
)


def test_error_base_class_is_frozen() -> None:
    error = Error(reason="some reason")
    with pytest.raises(FrozenInstanceError):
        error.reason = "other reason"  # type: ignore[misc]


def test_error_base_class_stores_reason() -> None:
    error = Error(reason="some reason")
    assert error.reason == "some reason"


def test_product_does_not_exist_error_defaults() -> None:
    error = ProductDoesNotExistError()
    assert error.reason == "Product does not exist"
    assert error.id is None
    assert error.name is None


def test_product_does_not_exist_error_with_id() -> None:
    product_id = uuid7()
    error = ProductDoesNotExistError(id=product_id)
    assert error.reason == "Product does not exist"
    assert error.id == product_id
    assert error.name is None


def test_product_error_stores_reason() -> None:
    error = ProductError(reason="Product does not exist")
    assert error.reason == "Product does not exist"


def test_product_id_already_exists_error() -> None:
    product_id = uuid7()
    error = ProductIdAlreadyExistsError(id=product_id)
    assert error.reason == "ID already exists"
    assert error.id == product_id


def test_product_in_deprecated_status_error_defaults() -> None:
    error = ProductInDeprecatedStatusError()
    assert error.reason == "Product is in deprecated status"
    assert error.id is None


def test_product_in_deprecated_status_error_with_id() -> None:
    product_id = uuid7()
    error = ProductInDeprecatedStatusError(id=product_id)
    assert error.reason == "Product is in deprecated status"
    assert error.id == product_id


def test_product_in_draft_status_error_defaults() -> None:
    error = ProductInDraftStatusError()
    assert error.reason == "Product is in draft status"
    assert error.id is None


def test_product_in_draft_status_error_with_id() -> None:
    product_id = uuid7()
    error = ProductInDraftStatusError(id=product_id)
    assert error.reason == "Product is in draft status"
    assert error.id == product_id


def test_product_name_already_exists_error() -> None:
    error = ProductNameAlreadyExistsError(name="My Product")
    assert error.reason == "Name already exists"
    assert error.name == "My Product"


def test_product_payload_update_error_deprecated() -> None:
    error = ProductPayloadUpdateError(
        reason="Cannot modify non-status attributes of a deprecated product",
        status="deprecated",
    )
    assert error.reason == "Cannot modify non-status attributes of a deprecated product"
    assert error.status == "deprecated"


def test_product_payload_update_error_published() -> None:
    error = ProductPayloadUpdateError(
        reason="Cannot modify non-status attributes of a published product",
        status="published",
    )
    assert error.reason == "Cannot modify non-status attributes of a published product"
    assert error.status == "published"


def test_product_status_deprecated_error_defaults() -> None:
    error = ProductStatusDeprecatedError()
    assert error.reason == "Product status is deprecated"
    assert error.id is None


def test_product_status_deprecated_error_with_id() -> None:
    product_id = uuid7()
    error = ProductStatusDeprecatedError(id=product_id)
    assert error.reason == "Product status is deprecated"
    assert error.id == product_id


def test_product_status_published_error_defaults() -> None:
    error = ProductStatusPublishedError()
    assert error.reason == "Product status is published"
    assert error.id is None


def test_product_status_published_error_with_id() -> None:
    product_id = uuid7()
    error = ProductStatusPublishedError(id=product_id)
    assert error.reason == "Product status is published"
    assert error.id == product_id


def test_product_status_update_error() -> None:
    error = ProductStatusUpdateError(
        reason="Cannot change status from published to draft",
        before="published",
        after="draft",
    )
    assert error.reason == "Cannot change status from published to draft"
    assert error.before == "published"
    assert error.after == "draft"


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


def test_user_does_not_exist_error_defaults() -> None:
    error = UserDoesNotExistError()
    assert error.reason == "User does not exist"
    assert error.id is None
    assert error.email is None


def test_user_does_not_exist_error_with_id() -> None:
    user_id = uuid7()
    error = UserDoesNotExistError(id=user_id)
    assert error.reason == "User does not exist"
    assert error.id == user_id
    assert error.email is None


def test_user_does_not_exist_error_with_email() -> None:
    error = UserDoesNotExistError(email="test@example.com")
    assert error.reason == "User does not exist"
    assert error.id is None
    assert error.email == "test@example.com"


def test_user_email_already_exists_error() -> None:
    error = UserEmailAlreadyExistsError(email="test@example.com")
    assert error.reason == "Email already exists"
    assert error.email == "test@example.com"


def test_user_error_stores_reason() -> None:
    error = UserError(reason="User does not exist")
    assert error.reason == "User does not exist"


def test_user_id_already_exists_error() -> None:
    user_id = uuid7()
    error = UserIdAlreadyExistsError(id=user_id)
    assert error.reason == "ID already exists"
    assert error.id == user_id
