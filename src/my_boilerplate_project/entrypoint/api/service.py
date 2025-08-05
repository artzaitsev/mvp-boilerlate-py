from typing import Union

from fastapi import FastAPI
import uvicorn

app = FastAPI()
@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/hello/{name}")
async def read_item(name: str):
    return {"item_id": name}

def main():
    uvicorn.run("my_boilerplate_project.entrypoint.api.service:app", host="0.0.0.0", port=8000, reload=True)