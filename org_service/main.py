from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from org_service.middleware.jwt_middleware import JWTMiddleware
from org_service.routes import auth_routes, secure_routes
from org_service.config import settings

middleware = [
    Middleware(SessionMiddleware, secret_key=settings.jwt_secret_key),
    Middleware(
        JWTMiddleware,
        exempt_paths=[
            "/auth/login",
            "/auth/callback",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
        ],
    ),
]

app = FastAPI(middleware=middleware)
app.include_router(auth_routes.router)
app.include_router(secure_routes.router)
