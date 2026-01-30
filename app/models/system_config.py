from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from datetime import datetime
from app.database.database import Base


class SystemConfiguration(Base):
    """
    Model for storing photovoltaic system configuration and metadata.
    
    Contains information about the PV system installation, capacity, location,
    and operational parameters.
    """
    __tablename__ = "system_configurations"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(String, unique=True, index=True, nullable=False, comment="Unique identifier for the PV system")
    name = Column(String, nullable=False, comment="System name or label")
    
    # System specifications
    capacity = Column(Float, nullable=True, comment="Installed capacity in kW")
    panel_count = Column(Integer, nullable=True, comment="Number of solar panels")
    panel_wattage = Column(Float, nullable=True, comment="Individual panel wattage in W")
    inverter_model = Column(String, nullable=True, comment="Inverter model/type")
    
    # Location information
    location = Column(String, nullable=True, comment="System location/address")
    latitude = Column(Float, nullable=True, comment="Latitude coordinate")
    longitude = Column(Float, nullable=True, comment="Longitude coordinate")
    
    # Operational parameters
    tilt_angle = Column(Float, nullable=True, comment="Panel tilt angle in degrees")
    azimuth = Column(Float, nullable=True, comment="Panel azimuth angle in degrees")
    is_active = Column(Boolean, default=True, nullable=False, comment="Whether the system is active")
    
    # Additional metadata
    installation_date = Column(DateTime, nullable=True, comment="System installation date")
    metadata = Column(JSON, nullable=True, comment="Additional metadata as JSON")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SystemConfiguration(system_id={self.system_id}, name={self.name}, capacity={self.capacity}kW)>"
