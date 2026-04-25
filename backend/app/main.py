from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import router as health_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.runs import router as runs_router
from app.api.v1.tickets import router as tickets_router


def create_app() -> FastAPI:
    app = FastAPI(title="supportflow-agent", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:5174",
            "http://localhost:5174",
            "http://127.0.0.1:4173",
            "http://localhost:4173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(tickets_router)
    app.include_router(runs_router)
    app.include_router(reviews_router)
    return app


app = create_app()
