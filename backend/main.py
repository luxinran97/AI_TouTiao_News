from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import users, favorite, history
from routers import news
from utils.exception_handlers import register_exception_handlers

app = FastAPI()

origins = [
    "http://localhost:5173",
]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"],allow_headers=["*"])

@app.get("/")
async def root():
    return {"message": "Hello World"}

app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)

app.include_router(history.router)

register_exception_handlers(app)