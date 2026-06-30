from contextlib import closing
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, event
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)
from trcks.oop import TupleWrapper

from app.data_structures.domain.product import (
    Product,
    ProductStatus,
)
from app.data_structures.domain.subscription import SubscriptionWithProduct
from app.data_structures.domain.user import UserWithSubscriptionsWithProducts

if TYPE_CHECKING:
    from sqlalchemy.engine.interfaces import DBAPIConnection
    from sqlalchemy.ext.asyncio import AsyncEngine
    from sqlalchemy.pool import ConnectionPoolEntry


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
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    user: Mapped[UserModel] = relationship(back_populates="subscriptions", init=False)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("product.id"))
    product: Mapped[ProductModel] = relationship(
        back_populates="subscriptions", init=False
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
        back_populates="user", default_factory=list, passive_deletes=True
    )

    def to_user_with_subscriptions_with_products(
        self,
    ) -> UserWithSubscriptionsWithProducts:
        subscriptions_with_products = (
            TupleWrapper.construct_from_iterable(self.subscriptions)
            .map(SubscriptionModel.to_subscription_with_product)
            .core
        )
        return UserWithSubscriptionsWithProducts(
            id=self.id,
            email=self.email,
            subscriptions_with_products=subscriptions_with_products,
        )


def _enable_foreign_keys(
    dbapi_connection: DBAPIConnection, _connection_record: ConnectionPoolEntry
) -> None:
    with closing(dbapi_connection.cursor()) as cursor:
        cursor.execute("PRAGMA foreign_keys=ON")


def enable_foreign_keys_for_engine(engine: AsyncEngine) -> None:
    """Enforce SQLite foreign keys on every connection of `engine`.

    SQLite enforces foreign keys per connection, so `PRAGMA foreign_keys=ON`
    must run for each DB-API connection rather than only once at startup.
    Registering a `connect` event listener applies the pragma to every pooled
    connection, keeping `ON DELETE CASCADE` behavior consistent.

    Call this once, right after the engine is created. The registration is
    idempotent: repeated calls on the same engine do not stack listeners.
    """
    if not event.contains(engine.sync_engine, "connect", _enable_foreign_keys):
        event.listen(engine.sync_engine, "connect", _enable_foreign_keys)


async def create_all_tables(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(_BaseModel.metadata.create_all)
