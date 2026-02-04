from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

try:
    from timezonefinder import TimezoneFinder
    tz_finder = TimezoneFinder()
except Exception:
    tz_finder = None

import os
try:
    import httpx
except Exception:
    httpx = None

from app.database.database import get_db
from app.models.system_config import SystemConfiguration
from app.schemas.system_config import (
    SystemConfigurationCreate,
    SystemConfigurationUpdate,
    SystemConfigurationResponse,
)

router = APIRouter(prefix="/systems", tags=["System Configuration"])


def _resolve_timezone(latitude: Optional[float], longitude: Optional[float]) -> Optional[str]:
    if latitude is None or longitude is None:
        return None
    if not tz_finder:
        return None
    return tz_finder.timezone_at(lat=latitude, lng=longitude)


def _get_location_name(latitude: Optional[float], longitude: Optional[float]) -> Optional[str]:
    """
    通过高德地图 API 获取坐标对应的地点名称（精确到街道级别）。
    如果 API 调用失败则返回 None。
    """
    if latitude is None or longitude is None:
        return None

    amap_key = os.getenv('AMAP_KEY')
    if not amap_key:
        return None
    if not httpx:
        return None

    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(
                'https://restapi.amap.com/v3/geocode/regeo',
                params={'location': f'{longitude},{latitude}', 'key': amap_key},
            )
            data = response.json()
            if data.get('status') == '1' and data.get('regeocode'):
                addr_comp = data['regeocode'].get('addressComponent', {})
                province = addr_comp.get('province', '')
                city = addr_comp.get('city', '')
                if isinstance(city, list):
                    city = ''
                district = addr_comp.get('district', '')
                township = addr_comp.get('township', '')
                parts = [province, city, district, township]
                return ''.join(filter(None, parts))
    except Exception as e:
        print(f"[警告] 获取地点名称失败: {e}")

    return None


@router.post("/", response_model=SystemConfigurationResponse, status_code=201)
def create_system_configuration(
    config: SystemConfigurationCreate,
    db: Session = Depends(get_db),
):
    existing = db.query(SystemConfiguration).filter(
        SystemConfiguration.system_id == config.system_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"System with ID '{config.system_id}' already exists")

    config_data = config.model_dump()
    if not config_data.get("timezone"):
        config_data["timezone"] = _resolve_timezone(
            config_data.get("latitude"), config_data.get("longitude")
        )

    if not config_data.get("location_name"):
        config_data["location_name"] = _get_location_name(
            config_data.get("latitude"), config_data.get("longitude")
        )

    db_config = SystemConfiguration(**config_data)
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.get("/", response_model=List[SystemConfigurationResponse])
def get_system_configurations(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
):
    query = db.query(SystemConfiguration)
    if is_active is not None:
        query = query.filter(SystemConfiguration.is_active == is_active)
    query = query.order_by(SystemConfiguration.created_at.desc())
    configurations = query.offset(offset).limit(limit).all()
    return configurations


@router.get("/{system_id}", response_model=SystemConfigurationResponse)
def get_system_configuration(system_id: str, db: Session = Depends(get_db)):
    config = db.query(SystemConfiguration).filter(SystemConfiguration.system_id == system_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="System configuration not found")
    return config


@router.put("/{system_id}", response_model=SystemConfigurationResponse)
def update_system_configuration(system_id: str, config_update: SystemConfigurationUpdate, db: Session = Depends(get_db)):
    config = db.query(SystemConfiguration).filter(SystemConfiguration.system_id == system_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="System configuration not found")

    update_data = config_update.model_dump(exclude_unset=True)
    if not update_data.get("timezone"):
        inferred = _resolve_timezone(update_data.get("latitude", config.latitude), update_data.get("longitude", config.longitude))
        if inferred:
            update_data["timezone"] = inferred

    if "latitude" in update_data or "longitude" in update_data:
        location_name = _get_location_name(update_data.get("latitude", config.latitude), update_data.get("longitude", config.longitude))
        if location_name:
            update_data["location_name"] = location_name

    for field, value in update_data.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)
    return config


@router.delete("/{system_id}", status_code=204)
def delete_system_configuration(system_id: str, db: Session = Depends(get_db)):
    config = db.query(SystemConfiguration).filter(SystemConfiguration.system_id == system_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="System configuration not found")
    db.delete(config)
    db.commit()
    return None
