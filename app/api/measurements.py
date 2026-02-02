from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.database.database import get_db
from app.models.measurement import Measurement
from app.models.system_config import SystemConfiguration
from app.schemas.measurement import (
    MeasurementCreate,
    MeasurementResponse,
    MeasurementBatch
)

router = APIRouter(prefix="/measurements", tags=["Measurements"])


def _compute_local_time(timestamp: Optional[datetime], tz_str: Optional[str]) -> Optional[datetime]:
    if not timestamp or not tz_str:
        return None
    try:
        return timestamp.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(tz_str))
    except Exception:
        return None


def _serialize_measurement(measurement: Measurement, tz_str: Optional[str]) -> dict:
    data = MeasurementResponse.model_validate(measurement).model_dump()
    data["local_time"] = _compute_local_time(measurement.timestamp, tz_str)
    return data


def _get_timezones(db: Session, system_ids: List[str]) -> dict:
    if not system_ids:
        return {}
    rows = (
        db.query(SystemConfiguration.system_id, SystemConfiguration.timezone)
        .filter(SystemConfiguration.system_id.in_(system_ids))
        .all()
    )
    return {system_id: tz for system_id, tz in rows}


@router.post("/", response_model=MeasurementResponse, status_code=201)
def create_measurement(
    measurement: MeasurementCreate,
    db: Session = Depends(get_db)
):
    """
    创建新的测量记录。
    
    接收来自光伏系统的单条传感器数据点。
    """
    # 如果未提供时间戳，则使用当前时间
    if measurement.timestamp is None:
        measurement.timestamp = datetime.utcnow()
    
    db_measurement = Measurement(**measurement.model_dump())
    db.add(db_measurement)
    db.commit()
    db.refresh(db_measurement)
    tz = (
        db.query(SystemConfiguration.timezone)
        .filter(SystemConfiguration.system_id == db_measurement.system_id)
        .scalar()
    )
    return _serialize_measurement(db_measurement, tz)


@router.post("/batch", response_model=List[MeasurementResponse], status_code=201)
def create_measurements_batch(
    batch: MeasurementBatch,
    db: Session = Depends(get_db)
):
    """
    批量创建多条测量记录。
    
    高效地一次性接收多条传感器数据点。
    """
    db_measurements = []
    
    for measurement in batch.measurements:
        # 如果未提供时间戳，则使用当前时间
        if measurement.timestamp is None:
            measurement.timestamp = datetime.utcnow()
        
        db_measurement = Measurement(**measurement.model_dump())
        db_measurements.append(db_measurement)
    
    db.add_all(db_measurements)
    db.commit()
    
    # 刷新所有对象以获取其 ID
    for db_measurement in db_measurements:
        db.refresh(db_measurement)
    
    tz_map = _get_timezones(db, [m.system_id for m in db_measurements])
    return [
        _serialize_measurement(m, tz_map.get(m.system_id))
        for m in db_measurements
    ]


@router.get("/", response_model=List[MeasurementResponse])
def get_measurements(
    system_id: Optional[str] = Query(None, description="Filter by system ID"),
    start_time: Optional[datetime] = Query(None, description="Start of time range"),
    end_time: Optional[datetime] = Query(None, description="End of time range"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    获取测量记录，支持可选过滤。
    
    支持按系统 ID 和时间范围过滤，以便高效进行时序查询。
    """
    query = db.query(Measurement)
    
    # 应用过滤条件
    if system_id:
        query = query.filter(Measurement.system_id == system_id)
    if start_time:
        query = query.filter(Measurement.timestamp >= start_time)
    if end_time:
        query = query.filter(Measurement.timestamp <= end_time)
    
    # 按时间戳降序排序（最新在前）
    query = query.order_by(Measurement.timestamp.desc())
    
    # 应用分页
    measurements = query.offset(offset).limit(limit).all()
    tz_map = _get_timezones(db, list({m.system_id for m in measurements}))

    return [
        _serialize_measurement(m, tz_map.get(m.system_id))
        for m in measurements
    ]


@router.get("/{measurement_id}", response_model=MeasurementResponse)
def get_measurement(
    measurement_id: int,
    db: Session = Depends(get_db)
):
    """
    根据 ID 获取指定测量记录。
    """
    measurement = db.query(Measurement).filter(Measurement.id == measurement_id).first()
    
    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found")
    
    tz = (
        db.query(SystemConfiguration.timezone)
        .filter(SystemConfiguration.system_id == measurement.system_id)
        .scalar()
    )
    return _serialize_measurement(measurement, tz)


@router.delete("/{measurement_id}", status_code=204)
def delete_measurement(
    measurement_id: int,
    db: Session = Depends(get_db)
):
    """
    根据 ID 删除指定测量记录。
    """
    measurement = db.query(Measurement).filter(Measurement.id == measurement_id).first()
    
    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found")
    
    db.delete(measurement)
    db.commit()
    
    return None
