from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class SystemConfigurationCreate(BaseModel):
    """Schema for creating a new system configuration."""
    system_id: str = Field(..., description="Unique identifier for the PV system")
    name: str = Field(..., description="System name or label")
    capacity: Optional[float] = Field(None, description="Installed capacity in kW")
    panel_count: Optional[int] = Field(None, description="Number of solar panels")
    panel_wattage: Optional[float] = Field(None, description="Individual panel wattage in W")
    inverter_model: Optional[str] = Field(None, description="Inverter model/type")
    location: Optional[str] = Field(None, description="System location/address")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude coordinate")
    tilt_angle: Optional[float] = Field(None, ge=0, le=90, description="Panel tilt angle in degrees")
    azimuth: Optional[float] = Field(None, ge=0, le=360, description="Panel azimuth angle in degrees")
    is_active: bool = Field(True, description="Whether the system is active")
    installation_date: Optional[datetime] = Field(None, description="System installation date")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata as JSON")

    class Config:
        json_schema_extra = {
            "example": {
                "system_id": "PV-001",
                "name": "Rooftop Solar Array",
                "capacity": 10.0,
                "panel_count": 40,
                "panel_wattage": 250.0,
                "inverter_model": "SolarEdge SE10000H",
                "location": "Building A, Main Campus",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "tilt_angle": 30.0,
                "azimuth": 180.0,
                "is_active": True,
                "installation_date": "2023-01-15T00:00:00Z"
            }
        }


class SystemConfigurationUpdate(BaseModel):
    """Schema for updating a system configuration."""
    name: Optional[str] = None
    capacity: Optional[float] = None
    panel_count: Optional[int] = None
    panel_wattage: Optional[float] = None
    inverter_model: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    tilt_angle: Optional[float] = Field(None, ge=0, le=90)
    azimuth: Optional[float] = Field(None, ge=0, le=360)
    is_active: Optional[bool] = None
    installation_date: Optional[datetime] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class SystemConfigurationResponse(BaseModel):
    """Schema for system configuration response."""
    id: int
    system_id: str
    name: str
    capacity: Optional[float] = None
    panel_count: Optional[int] = None
    panel_wattage: Optional[float] = None
    inverter_model: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    tilt_angle: Optional[float] = None
    azimuth: Optional[float] = None
    is_active: bool
    installation_date: Optional[datetime] = None
    extra_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
