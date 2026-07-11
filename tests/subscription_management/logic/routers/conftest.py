from collections.abc import Callable, Iterable, Mapping

import pytest

type StrMapping = Mapping[str, object]


def _get_id(d: StrMapping) -> str:
    return str(d["id"])


def _sorted_by_id(ds: Iterable[StrMapping]) -> list[StrMapping]:
    return sorted(ds, key=_get_id)


@pytest.fixture
def sorted_by_id() -> Callable[[Iterable[StrMapping]], list[StrMapping]]:
    return _sorted_by_id
