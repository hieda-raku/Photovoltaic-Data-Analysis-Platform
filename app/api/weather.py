from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Any, Dict, List, cast

from app.database.database import get_db
from app.models.weather import WeatherCurrent, WeatherForecast
from app.models.system_config import SystemConfiguration
from app.models.measurement import Measurement
from app.services.weather_service import (
    fetch_and_store_forecast as service_fetch_and_store_forecast,
    get_system_by_id,
)

router = APIRouter(prefix="/weather", tags=["Weather"])


class WeatherCurrentResponse(BaseModel):
    """实时气象数据响应（展平）"""
    system_id: str
    fetched_at: datetime
    shortwave_radiation: Optional[float] = None
    cloud_cover: Optional[float] = None
    temperature_2m: Optional[float] = None
    wind_speed_10m: Optional[float] = None
    
    class Config:
        from_attributes = True


class WeatherForecastResponse(BaseModel):
    """预报数据响应"""
    system_id: str
    days: int
    fetched_at: datetime
    hourly: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


def _flatten_current_data(db_record) -> WeatherCurrentResponse:
    """将数据库记录转换为展平的响应"""
    current_data = db_record.data.get('current', {})
    return WeatherCurrentResponse(
        system_id=db_record.system_id,
        fetched_at=db_record.fetched_at,
        shortwave_radiation=current_data.get('shortwave_radiation'),
        cloud_cover=current_data.get('cloud_cover'),
        temperature_2m=current_data.get('temperature_2m'),
        wind_speed_10m=current_data.get('wind_speed_10m'),
    )


def _flatten_forecast_data(db_record) -> WeatherForecastResponse:
    """将预报数据库记录转换为响应"""
    return WeatherForecastResponse(
        system_id=db_record.system_id,
        days=db_record.days,
        fetched_at=db_record.fetched_at,
        hourly=db_record.data.get('hourly'),
    )


def _to_api_payload(response_model):
    if hasattr(response_model, 'model_dump'):
        return response_model.model_dump()
    return response_model


def _get_latest_current_record(db: Session, system_id: str):
    return (
        db.query(WeatherCurrent)
        .filter(WeatherCurrent.system_id == system_id)
        .order_by(WeatherCurrent.fetched_at.desc())
        .first()
    )


def _get_latest_forecast_record(db: Session, system_id: str, days: int):
    return (
        db.query(WeatherForecast)
        .filter(
            WeatherForecast.system_id == system_id,
            WeatherForecast.days == days,
        )
        .order_by(WeatherForecast.fetched_at.desc())
        .first()
    )


def _get_system_location(db: Session, system_id: str):
    """获取系统位置信息"""
    config = get_system_by_id(db, system_id)
    if not config:
        raise ValueError(f"系统 {system_id} 不存在")
    return config


def fetch_and_store_forecast(db: Session, system_id: str, days: int = 1):
    """获取并存储单个系统的预报数据"""
    config = _get_system_location(db, system_id)
    return service_fetch_and_store_forecast(db, config, days=days)


def fetch_and_store_forecast_for_all_systems(db: Session, days: int = 1):
    """批量获取所有活跃系统的预报数据"""
    systems = (
        db.query(SystemConfiguration)
        .filter(SystemConfiguration.is_active == True)
        .all()
    )
    
    for system in systems:
        try:
            fetch_and_store_forecast(db, str(system.system_id), days=days)
            print(f"✅ 已更新 {system.system_id} 的预报数据")
        except Exception as e:
            print(f"❌ {system.system_id} 预报更新失败: {e}")


@router.get("/current", response_model=WeatherCurrentResponse)
def get_current_weather(
    system_id: str = Query(..., description="系统 ID"),
    db: Session = Depends(get_db)
):
    """
    获取系统的实时气象数据（基于经纬度，Open-Meteo）。
    """
    latest = _get_latest_current_record(db, system_id)
    if not latest:
        raise HTTPException(status_code=404, detail="No cached current weather")

    return _flatten_current_data(latest)


@router.get("/forecast", response_model=WeatherForecastResponse)
def get_weather_forecast(
    system_id: str = Query(..., description="系统 ID"),
    days: int = Query(2, ge=1, le=2, description="预报天数"),
    db: Session = Depends(get_db)
):
    """
    获取系统的气象预报数据（基于经纬度，Open-Meteo）。
    """
    latest = _get_latest_forecast_record(db, system_id, days)
    if not latest:
        raise HTTPException(status_code=404, detail="No cached forecast")

    return _flatten_forecast_data(latest)


# 缓存只读端点：仅从数据库读取，不触发外部拉取
@router.get("/current_cached", response_model=WeatherCurrentResponse)
def get_current_weather_cached(
    system_id: str = Query(..., description="系统 ID"),
    db: Session = Depends(get_db),
):
    """
    只从数据库返回最近一次的实时气象记录（不触发 Open-Meteo 拉取）。
    """
    latest = _get_latest_current_record(db, system_id)
    if not latest:
        raise HTTPException(status_code=404, detail="No cached current weather")
    try:
        return _to_api_payload(_flatten_current_data(latest))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/forecast_cached", response_model=WeatherForecastResponse)
def get_weather_forecast_cached(
    system_id: str = Query(..., description="系统 ID"),
    days: int = Query(2, ge=1, le=2, description="预报天数"),
    db: Session = Depends(get_db),
):
    """
    只从数据库返回最近一次的预报记录（不触发 Open-Meteo 拉取）。
    """
    latest = _get_latest_forecast_record(db, system_id, days)
    if not latest:
        raise HTTPException(status_code=404, detail="No cached forecast")
    try:
        return _to_api_payload(_flatten_forecast_data(latest))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 新端点：获取指定时间范围内的实际辐射测量数据
class MeasuredRadiationResponse(BaseModel):
    """测量的辐射数据响应"""
    timestamp: datetime
    irradiance: Optional[float]
    local_time: Optional[datetime] = None
    
    class Config:
        from_attributes = True


@router.get("/measured_radiation", response_model=List[MeasuredRadiationResponse])
def get_measured_radiation(
    system_id: str = Query(..., description="系统 ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间（本地时间 Asia/Shanghai）"),
    end_time: Optional[datetime] = Query(None, description="结束时间（本地时间 Asia/Shanghai）"),
    db: Session = Depends(get_db),
):
    """
    获取指定系统和时间范围内的实际辐射测量数据。
    
    用于与气象预报数据对比，显示实测值与预测值的差异。
    """
    query = db.query(Measurement).filter(Measurement.system_id == system_id)
    
    # 应用时间过滤
    if start_time:
        query = query.filter(Measurement.timestamp >= start_time)
    if end_time:
        query = query.filter(Measurement.timestamp <= end_time)
    
    # 按时间戳升序排序
    measurements = query.order_by(Measurement.timestamp.asc()).all()
    
    result = []
    for measurement in measurements:
        ts = cast(Optional[datetime], measurement.timestamp)
        irr = cast(Optional[float], measurement.irradiance)
        if ts is None:
            continue
        item = MeasuredRadiationResponse(
            timestamp=ts,
            irradiance=irr,
            local_time=ts,  # 数据库已存储本地时间（naive datetime），直接使用
        )
        result.append(item)
    
    return result
