from uuid import uuid7

from subscription_management.data_structures.domain.user import (
    UserDoesNotExistError,
    UserEmailAlreadyExistsError,
    UserIdAlreadyExistsError,
)


def test_user_does_not_exist_error_defaults() -> None:
    error = UserDoesNotExistError()
    assert error.id is None
    assert error.email is None


def test_user_does_not_exist_error_with_id() -> None:
    user_id = uuid7()
    error = UserDoesNotExistError(id=user_id)
    assert error.id == user_id
    assert error.email is None


def test_user_does_not_exist_error_with_email() -> None:
    error = UserDoesNotExistError(email="test@example.com")
    assert error.id is None
    assert error.email == "test@example.com"


def test_user_email_already_exists_error() -> None:
    error = UserEmailAlreadyExistsError(email="test@example.com")
    assert error.email == "test@example.com"


def test_user_id_already_exists_error() -> None:
    user_id = uuid7()
    error = UserIdAlreadyExistsError(id=user_id)
    assert error.id == user_id
