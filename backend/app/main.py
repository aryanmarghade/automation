from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import api_router
import app.tools.init_tools # Ensure tools are registered

from app.services.scheduler_service import SchedulerManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup DB tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Start Scheduler and reload active jobs from SQLite
    scheduler_mgr = SchedulerManager.get_instance()
    scheduler_mgr.start()
    await scheduler_mgr.reload_all_schedules()
    
    yield
    scheduler_mgr.shutdown()
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Workspace for direct artifact download/viewing
app.mount("/artifacts", StaticFiles(directory=str(settings.WORKSPACE_DIR)), name="artifacts")

# Mount API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "workspace": str(settings.WORKSPACE_DIR)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
