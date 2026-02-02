from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from datetime import datetime
from app.database.database import Base


class SystemConfiguration(Base):
    """
    用于存储光伏系统配置与元数据的模型。
    
    包含光伏系统的安装、容量、位置以及运行参数等信息。
    """
    __tablename__ = "system_configurations"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(String, unique=True, index=True, nullable=False, comment="光伏系统唯一标识")
    name = Column(String, nullable=False, comment="系统名称或标签")
    
    # 系统规格
    capacity = Column(Float, nullable=True, comment="装机容量（kW）")
    panel_count = Column(Integer, nullable=True, comment="光伏板数量")
    panel_wattage = Column(Float, nullable=True, comment="单块组件功率（W）")
    inverter_model = Column(String, nullable=True, comment="逆变器型号/类型")
    
    # 位置信息
    location = Column(String, nullable=True, comment="系统位置/地址")
    latitude = Column(Float, nullable=True, comment="纬度坐标")
    longitude = Column(Float, nullable=True, comment="经度坐标")
    timezone = Column(String, nullable=True, comment="IANA 时区标识（如 Asia/Shanghai）")
    
    # 运行参数
    tilt_angle = Column(Float, nullable=True, comment="组件倾角（度）")
    azimuth = Column(Float, nullable=True, comment="组件方位角（度）")
    is_active = Column(Boolean, default=True, nullable=False, comment="系统是否启用")
    
    # 其他元数据
    installation_date = Column(DateTime, nullable=True, comment="系统安装日期")
    extra_metadata = Column(JSON, nullable=True, comment="附加元数据（JSON）")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SystemConfiguration(system_id={self.system_id}, name={self.name}, capacity={self.capacity}kW)>"
