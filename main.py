from fastapi import FastAPI, HTTPException
import aioredis
import uvicorn

app = FastAPI()
redis = aioredis.from_url(
    "redis://redisserver.dist-prd:6379", encoding="utf-8", decode_responses=True
)


@app.on_event("startup")
async def startup_event():
    await redis.initialize()


@app.on_event("shutdown")
async def shutdown_event():
    await redis.close()


@app.post("/create/{key}")
async def create_key(key: str, value: str):
    if await redis.exists(key):
        raise HTTPException(status_code=400, detail="Key already exists")
    await redis.set(key, value)
    return {"key": key, "value": value}


@app.delete("/delete/{key}")
async def delete_key(key: str):
    if not await redis.exists(key):
        raise HTTPException(status_code=404, detail="Key not found")
    await redis.delete(key)
    return {"detail": "Key deleted"}


@app.get("/select/{key}")
async def select_key(key: str):
    value = await redis.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"key": key, "value": value}


if __name__ == "__main__":
    uvicorn.run(app="main:app", host="0.0.0.0", access_log=True, port=8080)
