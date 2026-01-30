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
    Create a new system configuration.
    
    Registers a new photovoltaic system with its specifications and parameters.
    """
    # Check if system_id already exists
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
    Retrieve all system configurations with optional filtering.
    """
    query = db.query(SystemConfiguration)
    
    # Apply filters
    if is_active is not None:
        query = query.filter(SystemConfiguration.is_active == is_active)
    
    # Order by creation date
    query = query.order_by(SystemConfiguration.created_at.desc())
    
    # Apply pagination
    configurations = query.offset(offset).limit(limit).all()
    
    return configurations


@router.get("/{system_id}", response_model=SystemConfigurationResponse)
def get_system_configuration(
    system_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific system configuration by system ID.
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
    Update a system configuration.
    
    Updates the specified fields of an existing system configuration.
    """
    config = db.query(SystemConfiguration).filter(
        SystemConfiguration.system_id == system_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="System configuration not found")
    
    # Update only provided fields
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
    Delete a system configuration.
    """
    config = db.query(SystemConfiguration).filter(
        SystemConfiguration.system_id == system_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="System configuration not found")
    
    db.delete(config)
    db.commit()
    
    return None
