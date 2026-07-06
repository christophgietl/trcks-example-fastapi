from dataclasses import FrozenInstanceError

import pytest

from subscription_management.data_structures.domain.errors import Error


def test_error_base_class_is_frozen() -> None:
    error = Error(reason="some reason")
    with pytest.raises(FrozenInstanceError):
        error.reason = "other reason"  # type: ignore[misc]


def test_error_base_class_stores_reason() -> None:
    error = Error(reason="some reason")
    assert error.reason == "some reason"
