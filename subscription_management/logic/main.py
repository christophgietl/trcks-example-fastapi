from fastapi import FastAPI

from subscription_management.logic.database import async_engine_lifespan
from subscription_management.logic.routers.health_router import health_router
from subscription_management.logic.routers.product_router import product_router
from subscription_management.logic.routers.subscription_router import (
    subscription_router,
)
from subscription_management.logic.routers.user_router import user_router

app = FastAPI(lifespan=async_engine_lifespan, title="trcks-example-fastapi")
app.include_router(health_router)
app.include_router(product_router)
app.include_router(subscription_router)
app.include_router(user_router)
