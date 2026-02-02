from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class SystemConfigurationCreate(BaseModel):
    """用于创建系统配置的模式。"""
    system_id: str = Field(..., description="光伏系统唯一标识")
    name: str = Field(..., description="系统名称或标签")
    capacity: Optional[float] = Field(None, description="装机容量（kW）")
    panel_count: Optional[int] = Field(None, description="光伏板数量")
    panel_wattage: Optional[float] = Field(None, description="单块组件功率（W）")
    inverter_model: Optional[str] = Field(None, description="逆变器型号/类型")
    location: Optional[str] = Field(None, description="系统位置/地址")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="纬度坐标")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="经度坐标")
    timezone: Optional[str] = Field(None, description="IANA 时区标识（如 Asia/Shanghai）")
    tilt_angle: Optional[float] = Field(None, ge=0, le=90, description="组件倾角（度）")
    azimuth: Optional[float] = Field(None, ge=0, le=360, description="组件方位角（度）")
    is_active: bool = Field(True, description="系统是否启用")
    installation_date: Optional[datetime] = Field(None, description="系统安装日期")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="附加元数据（JSON）")

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
    """用于更新系统配置的模式。"""
    name: Optional[str] = None
    capacity: Optional[float] = None
    panel_count: Optional[int] = None
    panel_wattage: Optional[float] = None
    inverter_model: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    timezone: Optional[str] = None
    tilt_angle: Optional[float] = Field(None, ge=0, le=90)
    azimuth: Optional[float] = Field(None, ge=0, le=360)
    is_active: Optional[bool] = None
    installation_date: Optional[datetime] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class SystemConfigurationResponse(BaseModel):
    """系统配置响应模式。"""
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
    timezone: Optional[str] = None
    tilt_angle: Optional[float] = None
    azimuth: Optional[float] = None
    is_active: bool
    installation_date: Optional[datetime] = None
    extra_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
