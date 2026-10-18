import os
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client

    redis_client = redis.from_url(
        REDIS_URL,
        decode_responses=True,
    )

    try:
        # Verify Redis is reachable during startup
        await redis_client.ping()
        yield
    finally:
        await redis_client.aclose()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Redis counter API is running"}


@app.get("/healthz")
async def healthz():
    try:
        await redis_client.ping()
        return {"status": "ok", "redis": "up"}
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Redis unavailable",
        )


@app.post("/hit/{key}")
async def hit(key: str):
    try:
        count = await redis_client.incr(f"hits:{key}")
        return {"key": key, "count": count}
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Redis unavailable",
        )


@app.get("/count/{key}")
async def count(key: str):
    try:
        value = await redis_client.get(f"hits:{key}")
        return {"key": key, "count": int(value) if value else 0}
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Redis unavailable",
        )
