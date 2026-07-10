"""
RootMC Mobile Companion API — entrypoint.

App factory, lifespan (seed), CORS, and router wiring. All request handlers
live under `routers/` and share helpers/config from `core.py`.
"""
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core import seed_if_empty
from routers import auth, market, portfolio, public, rewards


@asynccontextmanager
async def lifespan(app: FastAPI):
    await seed_if_empty()
    yield


app = FastAPI(title="RootMC Mobile API", version="1.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)

# All routes are mounted under /api — matches the k8s ingress + pytest paths.
api = APIRouter(prefix="/api")
api.include_router(public.router)
api.include_router(auth.router)
api.include_router(market.router)
api.include_router(portfolio.router)
api.include_router(rewards.router)

app.include_router(api)
