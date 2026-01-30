from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database.database import get_db
from app.models.measurement import Measurement
from app.schemas.measurement import (
    MeasurementCreate,
    MeasurementResponse,
    MeasurementBatch
)

router = APIRouter(prefix="/measurements", tags=["Measurements"])


@router.post("/", response_model=MeasurementResponse, status_code=201)
def create_measurement(
    measurement: MeasurementCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new measurement record.
    
    Ingests a single sensor data point from a photovoltaic system.
    """
    # If timestamp not provided, use current time
    if measurement.timestamp is None:
        measurement.timestamp = datetime.utcnow()
    
    db_measurement = Measurement(**measurement.model_dump())
    db.add(db_measurement)
    db.commit()
    db.refresh(db_measurement)
    return db_measurement


@router.post("/batch", response_model=List[MeasurementResponse], status_code=201)
def create_measurements_batch(
    batch: MeasurementBatch,
    db: Session = Depends(get_db)
):
    """
    Create multiple measurement records in batch.
    
    Efficiently ingests multiple sensor data points at once.
    """
    db_measurements = []
    
    for measurement in batch.measurements:
        # If timestamp not provided, use current time
        if measurement.timestamp is None:
            measurement.timestamp = datetime.utcnow()
        
        db_measurement = Measurement(**measurement.model_dump())
        db_measurements.append(db_measurement)
    
    db.add_all(db_measurements)
    db.commit()
    
    # Refresh all objects to get their IDs
    for db_measurement in db_measurements:
        db.refresh(db_measurement)
    
    return db_measurements


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
    Retrieve measurement records with optional filtering.
    
    Supports filtering by system ID and time range for efficient time-series queries.
    """
    query = db.query(Measurement)
    
    # Apply filters
    if system_id:
        query = query.filter(Measurement.system_id == system_id)
    if start_time:
        query = query.filter(Measurement.timestamp >= start_time)
    if end_time:
        query = query.filter(Measurement.timestamp <= end_time)
    
    # Order by timestamp descending (most recent first)
    query = query.order_by(Measurement.timestamp.desc())
    
    # Apply pagination
    measurements = query.offset(offset).limit(limit).all()
    
    return measurements


@router.get("/{measurement_id}", response_model=MeasurementResponse)
def get_measurement(
    measurement_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific measurement by ID.
    """
    measurement = db.query(Measurement).filter(Measurement.id == measurement_id).first()
    
    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found")
    
    return measurement


@router.delete("/{measurement_id}", status_code=204)
def delete_measurement(
    measurement_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a specific measurement by ID.
    """
    measurement = db.query(Measurement).filter(Measurement.id == measurement_id).first()
    
    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found")
    
    db.delete(measurement)
    db.commit()
    
    return None
