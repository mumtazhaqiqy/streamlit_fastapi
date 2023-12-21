# app.py (FastAPI)
from fastapi import FastAPI

app = FastAPI(root_path="/api")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items")
async def read_items():
    return [{"item_id": "Foo"}, {"item_id": "Bar"}]
