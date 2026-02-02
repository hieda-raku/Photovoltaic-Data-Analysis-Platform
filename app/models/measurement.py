from sqlalchemy import Column, Integer, Float, String, DateTime, Index
from datetime import datetime
from app.database.database import Base


class Measurement(Base):
    """
    用于存储光伏系统时序传感器数据的模型。
    
    存储来自太阳能板与监控设备的电压、电流、功率输出、辐照度、温度等测量值。
    """
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(String, index=True, nullable=False, comment="光伏系统唯一标识")
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="测量时间戳")
    
    # 环境测量
    irradiance = Column(Float, nullable=True, comment="太阳辐照度（W/m²）")
    temperature = Column(Float, nullable=True, comment="组件温度（°C）")
    ambient_temperature = Column(Float, nullable=True, comment="环境温度（°C）")
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 复合索引用于高效时序查询
    __table_args__ = (
        Index('ix_measurements_system_timestamp', 'system_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<Measurement(id={self.id}, system_id={self.system_id}, timestamp={self.timestamp})>"
