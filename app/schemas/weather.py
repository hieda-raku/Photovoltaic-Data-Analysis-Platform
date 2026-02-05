from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Dict


class WeatherCurrentResponse(BaseModel):
    """实时气象数据响应。"""
    system_id: str
    fetched_at: datetime
    data: Dict[str, Any] = Field(..., description="Open-Meteo 实时数据原始响应")

    class Config:
        orm_mode = True


class WeatherForecastResponse(BaseModel):
    """气象预报数据响应。"""
    system_id: str
    days: int
    fetched_at: datetime
    data: Dict[str, Any] = Field(..., description="Open-Meteo 预报数据原始响应")

    class Config:
        orm_mode = True
