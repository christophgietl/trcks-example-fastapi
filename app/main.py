from fastapi import FastAPI

from app.database import lifespan
from app.logic.routers.health_router import health_router
from app.logic.routers.product_router import product_router
from app.logic.routers.subscription_router import subscription_router
from app.logic.routers.user_router import user_router

app = FastAPI(lifespan=lifespan, title="trcks-example-fastapi")
app.include_router(health_router)
app.include_router(product_router)
app.include_router(subscription_router)
app.include_router(user_router)
