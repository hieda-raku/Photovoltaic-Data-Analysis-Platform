from sqlalchemy import Column, Integer, Float, String, DateTime, Index
from datetime import datetime
from app.database.database import Base


class Measurement(Base):
    """
    Model for storing time-series sensor data from photovoltaic systems.
    
    Stores measurements like voltage, current, power output, irradiance, and temperature
    from solar panels and monitoring equipment.
    """
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(String, index=True, nullable=False, comment="Unique identifier for the PV system")
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="Measurement timestamp")
    
    # Electrical measurements
    voltage = Column(Float, nullable=True, comment="Voltage in Volts (V)")
    current = Column(Float, nullable=True, comment="Current in Amperes (A)")
    power = Column(Float, nullable=True, comment="Power output in Watts (W)")
    
    # Environmental measurements
    irradiance = Column(Float, nullable=True, comment="Solar irradiance in W/m²")
    temperature = Column(Float, nullable=True, comment="Module temperature in Celsius (°C)")
    ambient_temperature = Column(Float, nullable=True, comment="Ambient temperature in Celsius (°C)")
    
    # Additional fields
    energy = Column(Float, nullable=True, comment="Energy in Watt-hours (Wh)")
    efficiency = Column(Float, nullable=True, comment="System efficiency as percentage")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Composite index for efficient time-series queries
    __table_args__ = (
        Index('ix_measurements_system_timestamp', 'system_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<Measurement(id={self.id}, system_id={self.system_id}, timestamp={self.timestamp}, power={self.power}W)>"
