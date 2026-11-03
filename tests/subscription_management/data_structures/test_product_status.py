import pytest

from subscription_management.data_structures.domain.product import ProductStatus


class TestProductStatus:
    @pytest.mark.parametrize(
        ("left", "right", "left_is_earlier"),
        [
            (ProductStatus.DRAFT, ProductStatus.DRAFT, False),
            (ProductStatus.DRAFT, ProductStatus.PUBLISHED, True),
            (ProductStatus.DRAFT, ProductStatus.DEPRECATED, True),
            (ProductStatus.PUBLISHED, ProductStatus.DRAFT, False),
            (ProductStatus.PUBLISHED, ProductStatus.PUBLISHED, False),
            (ProductStatus.PUBLISHED, ProductStatus.DEPRECATED, True),
            (ProductStatus.DEPRECATED, ProductStatus.DRAFT, False),
            (ProductStatus.DEPRECATED, ProductStatus.PUBLISHED, False),
            (ProductStatus.DEPRECATED, ProductStatus.DEPRECATED, False),
        ],
    )
    def test_comparisons_reflect_the_lifecycle(
        self, left: ProductStatus, right: ProductStatus, *, left_is_earlier: bool
    ) -> None:
        identical = left is right

        assert (left < right) == left_is_earlier
        assert (left <= right) == (left_is_earlier or identical)
        assert (left == right) == identical
        assert (right >= left) == (left_is_earlier or identical)
        assert (right > left) == left_is_earlier

    @pytest.mark.parametrize("status", ProductStatus)
    def test_comparisons_with_non_members_raise_type_error(
        self,
        status: ProductStatus,
    ) -> None:
        non_member = "draft"
        with pytest.raises(TypeError):
            _ = status < non_member
        with pytest.raises(TypeError):
            _ = status <= non_member
        with pytest.raises(TypeError):
            _ = status >= non_member
        with pytest.raises(TypeError):
            _ = status > non_member

    def test_statuses_sort_by_lifecycle(self) -> None:
        statuses = (
            ProductStatus.DEPRECATED,
            ProductStatus.DRAFT,
            ProductStatus.PUBLISHED,
        )
        assert sorted(statuses) == [
            ProductStatus.DRAFT,
            ProductStatus.PUBLISHED,
            ProductStatus.DEPRECATED,
        ]
        assert min(statuses) is ProductStatus.DRAFT
        assert max(statuses) is ProductStatus.DEPRECATED
