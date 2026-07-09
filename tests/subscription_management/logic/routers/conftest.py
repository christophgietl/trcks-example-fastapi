from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


type StrDict = dict[str, object]


def _get_id(d: StrDict) -> str:
    return str(d["id"])


def _sorted_by_id(ds: Iterable[StrDict]) -> list[StrDict]:
    return sorted(ds, key=_get_id)


@pytest.fixture
def sorted_by_id() -> Callable[[Iterable[StrDict]], list[StrDict]]:
    return _sorted_by_id
