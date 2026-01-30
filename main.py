from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import measurements, systems
from app.database.database import init_db

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
