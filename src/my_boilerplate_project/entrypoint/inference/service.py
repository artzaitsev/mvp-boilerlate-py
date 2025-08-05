import asyncio
import logging

from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager

from .di import model
from my_boilerplate_project.lib.flex_batcher import SyncPoolBatcher


class Input(BaseModel):
    text: str

class Input2(BaseModel):
    text: str


batcher: SyncPoolBatcher[str, int] = SyncPoolBatcher()


@asynccontextmanager
async def lifespan(srv: FastAPI):
    shutdown_event = asyncio.Event()

    worker = batcher.run(
        worker_fn=model.predict,
        shutdown_event=shutdown_event,
    )
    yield

    shutdown_event.set()
    try:
        await worker
        logging.getLogger("uvicorn").info(f"Batcher shutdown complete: {worker.done()}")
    except asyncio.CancelledError:
        logging.getLogger("uvicorn").warning("Batcher shutdown was cancelled")
    finally:
        batcher.shutdown()


app = FastAPI(lifespan=lifespan)


@app.post("/predict")
async def predict(req: Input):
    try:
        res = await batcher.process(req.text)
    except asyncio.TimeoutError:
        return {"error": "Prediction timeout"}
    except Exception as e:
        return {"error": "Internal server error"}

    return {"result": res}
