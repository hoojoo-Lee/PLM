from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from database import Base, engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="PLM Backend",
    description="轻量级 PLM 后端服务",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/", tags=["Health"])
def read_root():
    return {"status": "ok", "message": "PLM backend is running."}


@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    return {"status": "healthy", "database": "connected"}


# include routers
from routers.project_api import router as project_router
from routers.part_api import router as part_router

app.include_router(project_router)
app.include_router(part_router)
