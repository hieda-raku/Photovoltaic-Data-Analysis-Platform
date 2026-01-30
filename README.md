# Photovoltaic Data Analysis Platform

A minimal backend service for photovoltaic monitoring systems built with Python 3.11, FastAPI, PostgreSQL, and SQLAlchemy.

## Overview

This platform provides a REST API for ingesting and managing time-series sensor data from photovoltaic (solar panel) systems. It includes database models for measurements and system configurations, along with a calculation module for PV performance analytics.

## Features

- **REST API**: FastAPI-based endpoints for data ingestion and retrieval
- **Time-Series Data**: Efficient storage and querying of sensor measurements
- **System Management**: Configuration management for multiple PV systems
- **Performance Calculations**: Placeholder module for PV analytics (efficiency, performance ratio, etc.)
- **Auto-Documentation**: Interactive API documentation at `/docs` and `/redoc`

## Technology Stack

- **Python 3.11**: Modern Python with latest features
- **FastAPI**: High-performance async web framework
- **PostgreSQL**: Robust relational database for time-series data
- **SQLAlchemy**: ORM for database interactions
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server for running the application

## Project Structure

```
.
├── app/
│   ├── api/                    # API route handlers
│   │   ├── measurements.py     # Measurement endpoints
│   │   └── systems.py          # System configuration endpoints
│   ├── calculations/           # PV performance calculation module
│   │   └── pv_performance.py   # Performance calculation functions
│   ├── database/               # Database configuration
│   │   └── database.py         # SQLAlchemy setup and session management
│   ├── models/                 # Database models
│   │   ├── measurement.py      # Measurement model
│   │   └── system_config.py    # System configuration model
│   └── schemas/                # Pydantic schemas
│       ├── measurement.py      # Measurement request/response schemas
│       └── system_config.py    # System configuration schemas
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Installation

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/hieda-raku/Photovoltaic-Data-Analysis-Platform.git
   cd Photovoltaic-Data-Analysis-Platform
   ```

2. **Create a virtual environment**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database**
   ```bash
   # Create database
   createdb photovoltaic_db
   
   # Or using psql
   psql -U postgres
   CREATE DATABASE photovoltaic_db;
   ```

5. **Configure environment variables** (optional)
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

6. **Run the application**
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Measurements

- `POST /measurements/` - Create a single measurement
- `POST /measurements/batch` - Create multiple measurements in batch
- `GET /measurements/` - Retrieve measurements (with filtering)
- `GET /measurements/{id}` - Get a specific measurement
- `DELETE /measurements/{id}` - Delete a measurement

### System Configuration

- `POST /systems/` - Create a system configuration
- `GET /systems/` - List all system configurations
- `GET /systems/{system_id}` - Get a specific system configuration
- `PUT /systems/{system_id}` - Update a system configuration
- `DELETE /systems/{system_id}` - Delete a system configuration

### Health & Info

- `GET /` - API information
- `GET /health` - Health check endpoint

## Usage Examples

### Create a System Configuration

```bash
curl -X POST "http://localhost:8000/systems/" \
  -H "Content-Type: application/json" \
  -d '{
    "system_id": "PV-001",
    "name": "Rooftop Solar Array",
    "capacity": 10.0,
    "panel_count": 40,
    "latitude": 37.7749,
    "longitude": -122.4194
  }'
```

### Ingest Measurement Data

```bash
curl -X POST "http://localhost:8000/measurements/" \
  -H "Content-Type: application/json" \
  -d '{
    "system_id": "PV-001",
    "voltage": 48.5,
    "current": 12.3,
    "power": 596.55,
    "irradiance": 850.0,
    "temperature": 35.2
  }'
```

### Query Measurements

```bash
# Get recent measurements for a specific system
curl "http://localhost:8000/measurements/?system_id=PV-001&limit=10"

# Get measurements within a time range
curl "http://localhost:8000/measurements/?start_time=2024-01-01T00:00:00Z&end_time=2024-01-31T23:59:59Z"
```

## Data Models

### Measurement

Stores time-series sensor data:
- `system_id`: PV system identifier
- `timestamp`: Measurement time
- `voltage`: Voltage in Volts (V)
- `current`: Current in Amperes (A)
- `power`: Power output in Watts (W)
- `irradiance`: Solar irradiance in W/m²
- `temperature`: Module temperature in °C
- `ambient_temperature`: Ambient temperature in °C
- `energy`: Energy in Watt-hours (Wh)
- `efficiency`: System efficiency percentage

### System Configuration

Stores PV system metadata:
- `system_id`: Unique system identifier
- `name`: System name
- `capacity`: Installed capacity in kW
- `panel_count`: Number of panels
- `location`: Physical location
- `latitude`/`longitude`: Geographic coordinates
- `tilt_angle`: Panel tilt angle
- `azimuth`: Panel orientation
- `is_active`: System active status

## Performance Calculations Module

The `app/calculations/pv_performance.py` module provides placeholder functions for:

- **Efficiency Calculation**: Calculate system efficiency from power and irradiance
- **Performance Ratio**: Compare actual vs. theoretical energy output
- **Energy Estimation**: Estimate daily/monthly energy production
- **Anomaly Detection**: Detect unusual patterns in sensor data
- **Degradation Analysis**: Calculate panel degradation over time

Example usage:
```python
from app.calculations import calculate_efficiency, estimate_daily_energy

# Calculate efficiency
efficiency = calculate_efficiency(power=596.55, irradiance=850.0, area=25.0)

# Estimate daily energy production
daily_energy = estimate_daily_energy(capacity_kw=10.0, peak_sun_hours=5.0)
```

## Database Schema

The application automatically creates database tables on startup. Tables include:
- `measurements`: Time-series sensor data with composite index on (system_id, timestamp)
- `system_configurations`: PV system metadata with unique system_id

## Development

### Running in Development Mode

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The `--reload` flag enables auto-reloading when code changes.

### Database Migrations (Optional)

For production environments, consider using Alembic for database migrations:

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://postgres:postgres@localhost:5432/photovoltaic_db`)
- `APP_HOST`: Application host (default: `0.0.0.0`)
- `APP_PORT`: Application port (default: `8000`)

## Notes

- **No Authentication**: This is a minimal implementation without authentication. Add authentication middleware for production use.
- **No Frontend**: This is a backend-only service. The API can be consumed by any frontend application.
- **CORS Enabled**: CORS is enabled for all origins in development mode.

## Future Enhancements

Potential improvements for production deployment:
- Authentication and authorization (JWT, OAuth2)
- Rate limiting and request throttling
- Data aggregation and analytics endpoints
- Real-time data streaming (WebSockets)
- Advanced anomaly detection algorithms
- Integration with external weather APIs
- Alerting and notification system
- Data export functionality (CSV, Excel)
- Grafana/Prometheus integration for monitoring

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
