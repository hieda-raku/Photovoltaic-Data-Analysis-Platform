from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class MeasurementCreate(BaseModel):
    """用于创建测量记录的模式。"""
    system_id: str = Field(..., description="光伏系统唯一标识")
    timestamp: Optional[datetime] = Field(None, description="测量时间戳（默认当前时间）")
    voltage: Optional[float] = Field(None, description="电压（V）")
    current: Optional[float] = Field(None, description="电流（A）")
    power: Optional[float] = Field(None, description="功率输出（W）")
    irradiance: Optional[float] = Field(None, description="太阳辐照度（W/m²）")
    temperature: Optional[float] = Field(None, description="组件温度（°C）")
    ambient_temperature: Optional[float] = Field(None, description="环境温度（°C）")
    energy: Optional[float] = Field(None, description="能量（Wh）")
    efficiency: Optional[float] = Field(None, description="系统效率（%）")

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
    """测量记录响应模式。"""
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
    """用于批量创建测量记录的模式。"""
    measurements: list[MeasurementCreate] = Field(..., description="待创建的测量记录列表")

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
