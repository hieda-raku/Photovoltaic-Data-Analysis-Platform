from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class MeasurementCreate(BaseModel):
    """Schema for creating a new measurement."""
    system_id: str = Field(..., description="Unique identifier for the PV system")
    timestamp: Optional[datetime] = Field(None, description="Measurement timestamp (defaults to current time)")
    voltage: Optional[float] = Field(None, description="Voltage in Volts (V)")
    current: Optional[float] = Field(None, description="Current in Amperes (A)")
    power: Optional[float] = Field(None, description="Power output in Watts (W)")
    irradiance: Optional[float] = Field(None, description="Solar irradiance in W/m²")
    temperature: Optional[float] = Field(None, description="Module temperature in Celsius (°C)")
    ambient_temperature: Optional[float] = Field(None, description="Ambient temperature in Celsius (°C)")
    energy: Optional[float] = Field(None, description="Energy in Watt-hours (Wh)")
    efficiency: Optional[float] = Field(None, description="System efficiency as percentage")

    class Config:
        json_schema_extra = {
            "example": {
                "system_id": "PV-001",
                "timestamp": "2024-01-30T12:00:00Z",
                "voltage": 48.5,
                "current": 12.3,
                "power": 596.55,
                "irradiance": 850.0,
                "temperature": 35.2,
                "ambient_temperature": 25.0,
                "energy": 1500.0,
                "efficiency": 18.5
            }
        }


class MeasurementResponse(BaseModel):
    """Schema for measurement response."""
    id: int
    system_id: str
    timestamp: datetime
    voltage: Optional[float] = None
    current: Optional[float] = None
    power: Optional[float] = None
    irradiance: Optional[float] = None
    temperature: Optional[float] = None
    ambient_temperature: Optional[float] = None
    energy: Optional[float] = None
    efficiency: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MeasurementBatch(BaseModel):
    """Schema for batch measurement creation."""
    measurements: list[MeasurementCreate] = Field(..., description="List of measurements to create")

    class Config:
        json_schema_extra = {
            "example": {
                "measurements": [
                    {
                        "system_id": "PV-001",
                        "power": 596.55,
                        "irradiance": 850.0
                    },
                    {
                        "system_id": "PV-001",
                        "power": 610.25,
                        "irradiance": 870.0
                    }
                ]
            }
        }
