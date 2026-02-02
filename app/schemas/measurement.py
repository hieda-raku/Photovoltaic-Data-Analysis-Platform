from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class MeasurementCreate(BaseModel):
    """用于创建测量记录的模式。"""
    system_id: str = Field(..., description="光伏系统唯一标识")
    timestamp: Optional[datetime] = Field(None, description="测量时间戳（默认当前时间）")
    irradiance: Optional[float] = Field(None, description="太阳辐照度（W/m²）")
    temperature: Optional[float] = Field(None, description="组件温度（°C）")

    class Config:
        json_schema_extra = {
            "example": {
                "system_id": "PV-001",
                "timestamp": "2024-01-30T12:00:00Z",
                "irradiance": 850.0,
                "temperature": 35.2,
                "ambient_temperature": 25.0
            }
        }


class MeasurementResponse(BaseModel):
    """测量记录响应模式。"""
    id: int
    system_id: str
    timestamp: datetime
    local_time: Optional[datetime] = None
    irradiance: Optional[float] = None
    temperature: Optional[float] = None
    ambient_temperature: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MeasurementBatch(BaseModel):
    """用于批量创建测量记录的模式。"""
    measurements: list[MeasurementCreate] = Field(..., description="待创建的测量记录列表")

    class Config:
        json_schema_extra = {
            "example": {
                "measurements": [
                    {
                        "system_id": "PV-001",
                        "irradiance": 850.0
                    },
                    {
                        "system_id": "PV-001",
                        "irradiance": 870.0
                    }
                ]
            }
        }
