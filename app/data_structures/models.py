from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, text
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)

from app.data_structures.domain.product import (
    Product,
    ProductStatus,
)
from app.data_structures.domain.subscription import (
    SubscriptionWithProduct,
    SubscriptionWithUserIdAndProductId,
)
from app.data_structures.domain.user import (
    User,
    UserWithSubscriptionsWithProducts,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


class _BaseModel(DeclarativeBase, MappedAsDataclass):
    id: Mapped[UUID] = mapped_column(primary_key=True)


class ProductModel(_BaseModel):
    __tablename__ = "product"
    monthly_fee_in_euros: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    name: Mapped[str] = mapped_column(index=True, unique=True)
    status: Mapped[ProductStatus]
    subscriptions: Mapped[list[SubscriptionModel]] = relationship(
        back_populates="product", default_factory=list
    )

    @staticmethod
    def from_product(product: Product) -> ProductModel:
        return ProductModel(
            id=product.id,
            monthly_fee_in_euros=product.monthly_fee_in_euros,
            name=product.name,
            status=product.status,
        )

    def to_product(self) -> Product:
        return Product(
            id=self.id,
            monthly_fee_in_euros=self.monthly_fee_in_euros,
            name=self.name,
            status=self.status,
        )


class SubscriptionModel(_BaseModel):
    __tablename__ = "subscription"
    is_active: Mapped[bool]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"))
    user: Mapped[UserModel] = relationship(back_populates="subscriptions", init=False)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("product.id"))
    product: Mapped[ProductModel] = relationship(
        back_populates="subscriptions", init=False
    )

    @staticmethod
    def from_subscription_with_user_id_and_product_id(
        subscription: SubscriptionWithUserIdAndProductId,
    ) -> SubscriptionModel:
        return SubscriptionModel(
            id=subscription.id,
            is_active=subscription.is_active,
            user_id=subscription.user_id,
            product_id=subscription.product_id,
        )

    def to_subscription_with_product(self) -> SubscriptionWithProduct:
        return SubscriptionWithProduct(
            id=self.id,
            is_active=self.is_active,
            product=self.product.to_product(),
        )


class UserModel(_BaseModel):
    __tablename__ = "user"
    email: Mapped[str] = mapped_column(index=True, unique=True)
    subscriptions: Mapped[list[SubscriptionModel]] = relationship(
        back_populates="user", default_factory=list
    )

    @staticmethod
    def from_user(user: User) -> UserModel:
        return UserModel(id=user.id, email=user.email)

    def to_user_with_subscriptions_with_products(
        self,
    ) -> UserWithSubscriptionsWithProducts:
        subscriptions_with_products = tuple(
            subscription_model.to_subscription_with_product()
            for subscription_model in self.subscriptions
        )
        return UserWithSubscriptionsWithProducts(
            id=self.id,
            email=self.email,
            subscriptions_with_products=subscriptions_with_products,
        )


async def set_pragmas_and_create_all_tables(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        _ = await conn.execute(text("PRAGMA foreign_keys=ON"))
        await conn.run_sync(_BaseModel.metadata.create_all)
