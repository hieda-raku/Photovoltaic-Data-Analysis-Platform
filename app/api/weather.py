from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
import httpx

from app.database.database import get_db
from app.models.system_config import SystemConfiguration
from app.models.weather import WeatherCurrent, WeatherForecast
from app.schemas.weather import WeatherCurrentResponse, WeatherForecastResponse

router = APIRouter(prefix="/weather", tags=["Weather"])

OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"


def _get_system_location(db: Session, system_id: str) -> SystemConfiguration:
    config = (
        db.query(SystemConfiguration)
        .filter(SystemConfiguration.system_id == system_id)
        .first()
    )
    if not config:
        raise HTTPException(status_code=404, detail="System configuration not found")
    if config.latitude is None or config.longitude is None:
        raise HTTPException(status_code=400, detail="System latitude/longitude is required")
    return config


def _fetch_open_meteo(params: dict) -> dict:
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(OPEN_METEO_BASE, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Failed to fetch weather data") from exc


@router.get("/current/{system_id}", response_model=WeatherCurrentResponse)
def get_current_weather(
    system_id: str,
    db: Session = Depends(get_db)
):
    """
    获取系统的实时气象数据（基于经纬度，Open-Meteo）。
    """
    config = _get_system_location(db, system_id)
    params = {
        "latitude": config.latitude,
        "longitude": config.longitude,
        "current": "shortwave_radiation,cloud_cover,temperature_2m",
        "timezone": config.timezone or "auto",
    }
    data = _fetch_open_meteo(params)

    record = WeatherCurrent(
        system_id=system_id,
        fetched_at=datetime.utcnow(),
        data=data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/forecast/{system_id}", response_model=WeatherForecastResponse)
def get_weather_forecast(
    system_id: str,
    days: int = Query(1, ge=1, le=1, description="预报天数"),
    db: Session = Depends(get_db)
):
    """
    获取系统的气象预报数据（基于经纬度，Open-Meteo）。
    """
    config = _get_system_location(db, system_id)
    params = {
        "latitude": config.latitude,
        "longitude": config.longitude,
        "hourly": "shortwave_radiation,cloud_cover,wind_speed_10m,temperature_2m",
        "forecast_days": days,
        "timezone": config.timezone or "auto",
    }
    data = _fetch_open_meteo(params)

    record = WeatherForecast(
        system_id=system_id,
        days=days,
        fetched_at=datetime.utcnow(),
        data=data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
