# app.py (FastAPI)
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items")
async def read_items():
    return [{"item_id": "Foo"}, {"item_id": "Bar"}]
