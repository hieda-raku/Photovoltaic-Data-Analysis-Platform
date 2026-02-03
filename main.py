from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.api import measurements, systems
import app.api.weather as weather
from app.database.database import init_db, get_db
from app.models.measurement import Measurement
from app.models.system_config import SystemConfiguration
from app.schemas.measurement import MeasurementResponse

load_dotenv()

# 创建 FastAPI 应用
app = FastAPI(
    title="Photovoltaic Data Analysis Platform",
    description="""
    光伏监控系统的简易后端服务。
    
    ## 功能
    
    * **测量数据 API**：写入并查询光伏系统的时序传感器数据
    * **系统配置 API**：管理光伏系统配置与元数据
    * **性能计算**：光伏性能分析的占位模块
    
    ## 数据模型
    
    * **Measurement**：包含电压、电流、功率、辐照度、温度等时序数据
    * **System Configuration**：光伏系统规格、位置与运行参数
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.middleware("http")
async def log_http_requests(request: Request, call_next):
    """
    记录 HTTP 请求与响应信息（用于调试数据格式）。
    注意：仅用于测试/开发环境，生产环境请按需脱敏与限制日志体积。
    """
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


@app.on_event("startup")
async def startup_event():
    """
    应用启动时初始化数据库。
    若表不存在则创建。
    """
    init_db()


@app.get("/", tags=["Root"])
async def root():
    """
    根路由，提供 API 信息。
    """
    return {
        "message": "Photovoltaic Data Analysis Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "measurements": "/measurements",
            "systems": "/systems"
        }
    }


@app.get("/admin", tags=["Root"])
async def admin_page():
    return FileResponse("static/admin.html")


@app.post("/", response_model=MeasurementResponse, status_code=201, tags=["Root"])
async def ingest_from_device(request: Request, db: Session = Depends(get_db)):
    """
    兼容下位机固定上报路径的入口（POST /）。
    将下位机数据映射为测量记录并写入数据库。
    """
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

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
    data = MeasurementResponse.model_validate(db_measurement).model_dump()
    if tz:
        try:
            data["local_time"] = db_measurement.timestamp.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(tz))
        except Exception:
            data["local_time"] = None
    return data


@app.get("/health", tags=["Health"])
async def health_check():
    """
    健康检查接口。
    """
    return {
        "status": "healthy",
        "service": "photovoltaic-data-analysis-platform"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
