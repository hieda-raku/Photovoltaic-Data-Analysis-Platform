from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.database import get_db
from app.models.system_config import SystemConfiguration
from app.schemas.system_config import (
    SystemConfigurationCreate,
    SystemConfigurationUpdate,
    SystemConfigurationResponse
)

router = APIRouter(prefix="/systems", tags=["System Configuration"])


@router.post("/", response_model=SystemConfigurationResponse, status_code=201)
def create_system_configuration(
    config: SystemConfigurationCreate,
    db: Session = Depends(get_db)
):
    """
    创建新的系统配置。
    
    注册一个新的光伏系统及其规格与参数。
    """
    # 检查 system_id 是否已存在
    existing = db.query(SystemConfiguration).filter(
        SystemConfiguration.system_id == config.system_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"System with ID '{config.system_id}' already exists"
        )
    
    db_config = SystemConfiguration(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.get("/", response_model=List[SystemConfigurationResponse])
def get_system_configurations(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    获取所有系统配置，支持可选过滤。
    """
    query = db.query(SystemConfiguration)
    
    # 应用过滤条件
    if is_active is not None:
        query = query.filter(SystemConfiguration.is_active == is_active)
    
    # 按创建时间排序
    query = query.order_by(SystemConfiguration.created_at.desc())
    
    # 应用分页
    configurations = query.offset(offset).limit(limit).all()
    
    return configurations


@router.get("/{system_id}", response_model=SystemConfigurationResponse)
def get_system_configuration(
    system_id: str,
    db: Session = Depends(get_db)
):
    """
    根据系统 ID 获取指定系统配置。
    """
    config = db.query(SystemConfiguration).filter(
        SystemConfiguration.system_id == system_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="System configuration not found")
    
    return config


@router.put("/{system_id}", response_model=SystemConfigurationResponse)
def update_system_configuration(
    system_id: str,
    config_update: SystemConfigurationUpdate,
    db: Session = Depends(get_db)
):
    """
    更新系统配置。
    
    更新已有系统配置中的指定字段。
    """
    config = db.query(SystemConfiguration).filter(
        SystemConfiguration.system_id == system_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="System configuration not found")
    
    # 仅更新提供的字段
    update_data = config_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    return config


@router.delete("/{system_id}", status_code=204)
def delete_system_configuration(
    system_id: str,
    db: Session = Depends(get_db)
):
    """
    删除系统配置。
    """
    config = db.query(SystemConfiguration).filter(
        SystemConfiguration.system_id == system_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="System configuration not found")
    
    db.delete(config)
    db.commit()
    
    return None
