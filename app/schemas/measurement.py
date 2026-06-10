from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional


class MeasurementCreate(BaseModel):
    """用于创建测量记录的模式。"""
    system_id: str = Field(..., description="光伏系统唯一标识")
    timestamp: Optional[datetime] = Field(None, description="测量时间戳（默认当前时间）")
    irradiance: Optional[float] = Field(None, description="太阳辐照度（W/m²）")
    temperature: Optional[float] = Field(None, description="组件温度（°C）")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "system_id": "PV-001",
                "timestamp": "2024-01-30T12:00:00Z",
                "irradiance": 850.0,
                "temperature": 35.2,
            }
        }
    )


class MeasurementResponse(BaseModel):
    """测量记录响应模式。"""
    id: int
    system_id: str
    timestamp: datetime
    local_time: Optional[datetime] = None
    irradiance: Optional[float] = None
    temperature: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeasurementBatch(BaseModel):
    """用于批量创建测量记录的模式。"""
    measurements: list[MeasurementCreate] = Field(..., description="待创建的测量记录列表")

    model_config = ConfigDict(
        json_schema_extra={
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
    )
