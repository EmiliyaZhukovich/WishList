from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from app.routers.wishlist import router as wishlist_router
from app.routers.present import router as present_router
from app.routers.user import router as user_router
from app.database.database import init_db
from app.config import settings
from app.core.limit import limiter


app = FastAPI(
    title=settings.app_name,
    docs_url='/api/docs',
    redoc_url='/api/redoc',
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "RATE_LIMIT_EXCEEDED",
            "message": "Too many requests, slow down"
        }
    )

app.include_router(wishlist_router)
app.include_router(present_router)
app.include_router(user_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

@app.on_event('startup')
async def on_startup():
    await init_db()

@app.get('/')
async def root():
    return {
        "message":"Welcome to project",
        'docs':"api/docs",
    }

@app.get('/health')
async def health_check():
    return {'status':'healthy'}
