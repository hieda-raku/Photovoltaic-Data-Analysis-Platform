from sqlalchemy import Column, Integer, String, DateTime, JSON, Index
from datetime import datetime
from app.database.database import Base


class WeatherCurrent(Base):
    """
    存储系统的实时气象数据快照。
    时间戳使用Asia/Shanghai本地时间（UTC+8）。
    """
    __tablename__ = "weather_current"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(String, index=True, nullable=False, comment="光伏系统唯一标识")
    fetched_at = Column(DateTime, nullable=False, comment="拉取时间（本地时间）")
    data = Column(JSON, nullable=False, comment="Open-Meteo 实时数据原始响应")
    created_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_weather_current_system_fetched", "system_id", "fetched_at"),
    )


class WeatherForecast(Base):
    """
    存储系统的气象预报数据快照。
    时间戳使用Asia/Shanghai本地时间（UTC+8）。
    """
    __tablename__ = "weather_forecast"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(String, index=True, nullable=False, comment="光伏系统唯一标识")
    days = Column(Integer, nullable=False, comment="预报天数")
    fetched_at = Column(DateTime, nullable=False, comment="拉取时间（本地时间）")
    data = Column(JSON, nullable=False, comment="Open-Meteo 预报数据原始响应")
    created_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_weather_forecast_system_fetched", "system_id", "fetched_at"),
    )
