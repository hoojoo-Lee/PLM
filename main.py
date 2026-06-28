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
from fastapi.middleware.cors import CORSMiddleware

# 解除 CORS 跨域限制，允许前端网页访问后端 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有域名访问
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有请求方法 (GET, POST 等)
    allow_headers=["*"],  # 允许所有请求头
)

@app.get("/", tags=["Health"])
def read_root():
    return {"status": "ok", "message": "PLM backend is running."}


@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    return {"status": "healthy", "database": "connected"}


# include routers
from routers.product_api import router as product_router
from routers.project_api import router as project_router
from routers.bom_api import router as bom_router
from routers.document_api import router as document_router

app.include_router(product_router)
app.include_router(project_router)
app.include_router(bom_router)
app.include_router(document_router)
