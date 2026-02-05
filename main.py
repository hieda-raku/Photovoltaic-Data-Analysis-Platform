try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv():
        return None
import asyncio
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.api import measurements, systems
import app.api.weather as weather
from app.database.database import init_db, get_db, SessionLocal
from app.models.measurement import Measurement
from app.models.system_config import SystemConfiguration
from app.schemas.measurement import MeasurementResponse

load_dotenv()

# 创建 FastAPI 应用
app = FastAPI(
    title="Photovoltaic Data Analysis Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.middleware("http")
async def log_http_requests(request: Request, call_next):
    body = await request.body()
    body_text = body.decode("utf-8", errors="ignore")
    if len(body_text) > 2000:
        body_text = body_text[:2000] + "..."
    response = await call_next(request)
    print(
        f"[HTTP] {request.method} {request.url.path} | "
        f"status={response.status_code} | body={body_text}"
    )
    return response


# 配置 CORS（开发环境允许所有来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册 API 路由
app.include_router(measurements.router)
app.include_router(systems.router)
app.include_router(weather.router)

# Remove any accidental temporary admin routes from the registered routes
# (defensive: ensures removed trigger endpoint won't be exposed in OpenAPI)
try:
    app.router.routes = [
        r for r in app.router.routes if getattr(r, "path", None) != "/weather/trigger_current_fetch"
    ]
except Exception:
    pass



@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Photovoltaic Data Analysis Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "measurements": "/measurements",
            "systems": "/systems",
        },
    }


@app.get("/admin", tags=["Root"])
async def admin_page():
    return FileResponse("static/admin.html")


@app.get("/data-view", tags=["Root"])
async def data_view_page():
    return FileResponse("static/data-view.html")


@app.get("/weather-view", tags=["Root"])
async def weather_view_page():
    return FileResponse("static/weather-view.html")


@app.post("/", response_model=MeasurementResponse, status_code=201, tags=["Root"])
async def ingest_from_device(request: Request, db: Session = Depends(get_db)):
    """兼容下位机固定上报路径的入口（POST /）。将下位机数据映射为测量记录并写入数据库。"""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    system_id = payload.get("system_id")
    if not system_id:
        raise HTTPException(status_code=422, detail="system_id is required")

    timestamp = None
    ts = payload.get("ts")
    if isinstance(ts, (int, float)):
        timestamp = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).replace(tzinfo=None)

    params = payload.get("params") or {}
    measurement_data = {
        "system_id": system_id,
        "timestamp": timestamp,
        "temperature": params.get("Tbody"),
        "irradiance": params.get("NR"),
    }

    db_measurement = Measurement(**measurement_data)
    db.add(db_measurement)
    db.commit()
    db.refresh(db_measurement)

    tz = (
        db.query(SystemConfiguration.timezone)
        .filter(SystemConfiguration.system_id == db_measurement.system_id)
        .scalar()
    )

    data = MeasurementResponse.from_orm(db_measurement).dict()
    if tz and db_measurement.timestamp:
        try:
            data["local_time"] = db_measurement.timestamp.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(tz))
        except Exception:
            data["local_time"] = None

    return data


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "photovoltaic-data-analysis-platform"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
