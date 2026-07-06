from uuid import uuid7

from subscription_management.data_structures.domain.product import (
    ProductDoesNotExistError,
    ProductIdAlreadyExistsError,
    ProductInDeprecatedStatusError,
    ProductInDraftStatusError,
    ProductNameAlreadyExistsError,
    ProductPayloadUpdateError,
    ProductStatusDeprecatedError,
    ProductStatusPublishedError,
    ProductStatusUpdateError,
)


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
