from contextlib import asynccontextmanager
import os

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import Base, engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="PLM Backend",
    description="敏捷硬件 PLM 后端服务 - V4.0 架构",
    version="1.0.0",
    lifespan=lifespan,
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def read_root():
    return FileResponse("index.html")


@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    return {"status": "healthy", "database": "connected"}


from routers.product_api import router as product_router
from routers.customer_api import router as customer_router
from routers.bom_api import router as bom_router
from routers.project_api import router as project_router
from routers.document_api import router as document_router
from routers.gantt_api import router as gantt_router
from routers.tracker_api import router as tracker_router
from routers.risk_api import router as risk_router
from routers.npi_api import router as npi_router

app.include_router(product_router)
app.include_router(customer_router)
app.include_router(bom_router)
app.include_router(project_router)
app.include_router(document_router)
app.include_router(gantt_router)
app.include_router(tracker_router)
app.include_router(risk_router)
app.include_router(npi_router)

upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

app.mount("/", StaticFiles(directory=os.path.dirname(__file__), html=True), name="frontend")