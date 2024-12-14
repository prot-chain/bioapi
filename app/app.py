from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import Config, get_config
from api.v1 import router as v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ = get_config()

    yield


app = FastAPI(
    title="BioAPI service",
    lifespan=lifespan,
    version="1.0"
)

# CORS Middleware
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(v1_router, prefix="/api/v1")


@app.get("/health")
def read_settings(cfg: Annotated[Config, Depends(get_config)]):
    return {
        "service":  "up"
    }
