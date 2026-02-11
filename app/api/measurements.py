from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from app.database.database import get_db
from app.models.measurement import Measurement
from app.schemas.measurement import (
    MeasurementCreate,
    MeasurementResponse,
    MeasurementBatch
)

router = APIRouter(prefix="/measurements", tags=["Measurements"])

SYSTEM_TIMEZONE = "Asia/Shanghai"


def _get_local_now() -> datetime:
    return datetime.now(ZoneInfo(SYSTEM_TIMEZONE)).replace(tzinfo=None)


def _serialize_measurement(measurement: Measurement) -> dict:
    data = MeasurementResponse.from_orm(measurement).dict()
    data["local_time"] = measurement.timestamp
    return data


@router.post("/", response_model=MeasurementResponse, status_code=201)
def create_measurement(
    measurement: MeasurementCreate,
    db: Session = Depends(get_db)
):
    """
    创建新的测量记录。
    接收来自光伏系统的单条传感器数据点。
    """
    # 如果未提供时间戳，则使用本地时间（Asia/Shanghai）
    if measurement.timestamp is None:
        measurement.timestamp = _get_local_now()

    data = measurement.dict()
    data["created_at"] = _get_local_now()

    db_measurement = Measurement(**data)
    db.add(db_measurement)
    db.commit()
    db.refresh(db_measurement)

    return _serialize_measurement(db_measurement)


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
        # 如果未提供时间戳，则使用本地时间（Asia/Shanghai）
        if measurement.timestamp is None:
            measurement.timestamp = _get_local_now()

        data = measurement.dict()
        data["created_at"] = _get_local_now()

        db_measurement = Measurement(**data)
        db_measurements.append(db_measurement)

    db.add_all(db_measurements)
    db.commit()

    # 刷新所有对象以获取其 ID
    for db_measurement in db_measurements:
        db.refresh(db_measurement)

    return [
        _serialize_measurement(m)
        for m in db_measurements
    ]


@router.get("/", response_model=List[MeasurementResponse])
def get_measurements(
    system_id: Optional[str] = Query(None, description="按系统 ID 过滤"),
    start_time: Optional[datetime] = Query(None, description="时间范围开始（本地时间 Asia/Shanghai）"),
    end_time: Optional[datetime] = Query(None, description="时间范围结束（本地时间 Asia/Shanghai）"),
    limit: int = Query(100, ge=1, le=1440, description="最大返回记录数（一分钟一条数据，一天上限1440条）"),
    offset: int = Query(0, ge=0, description="分页偏移量"),
    db: Session = Depends(get_db)
):
    """
    获取测量记录，支持可选过滤。

    支持按系统 ID 和时间范围过滤，以便高效进行时序查询。
    注意：数据库存储和查询都使用本地时间（Asia/Shanghai），无需时区转换。
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

    return [
        _serialize_measurement(m)
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

    return _serialize_measurement(measurement)


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
