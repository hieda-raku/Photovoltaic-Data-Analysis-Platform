from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import measurements, systems
from app.database.database import init_db

# Create FastAPI application
app = FastAPI(
    title="Photovoltaic Data Analysis Platform",
    description="""
    A minimal backend service for photovoltaic monitoring system.
    
    ## Features
    
    * **Measurements API**: Ingest and retrieve time-series sensor data from PV systems
    * **System Configuration API**: Manage PV system configurations and metadata
    * **Performance Calculations**: Placeholder module for PV performance analytics
    
    ## Data Models
    
    * **Measurement**: Time-series data including voltage, current, power, irradiance, temperature
    * **System Configuration**: PV system specifications, location, and operational parameters
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(measurements.router)
app.include_router(systems.router)


@app.on_event("startup")
async def startup_event():
    """
    Initialize database on application startup.
    Creates all tables if they don't exist.
    """
    init_db()


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint providing API information.
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
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "photovoltaic-data-analysis-platform"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
