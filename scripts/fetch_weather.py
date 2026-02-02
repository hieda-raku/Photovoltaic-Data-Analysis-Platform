from datetime import datetime
import httpx

from app.database.database import SessionLocal
from app.models.system_config import SystemConfiguration
from app.models.weather import WeatherCurrent, WeatherForecast

OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"


def fetch_open_meteo(params: dict) -> dict:
    with httpx.Client(timeout=15.0) as client:
        response = client.get(OPEN_METEO_BASE, params=params)
        response.raise_for_status()
        return response.json()


def main() -> int:
    db = SessionLocal()
    try:
        systems = (
            db.query(SystemConfiguration)
            .filter(SystemConfiguration.is_active.is_(True))
            .filter(SystemConfiguration.latitude.isnot(None))
            .filter(SystemConfiguration.longitude.isnot(None))
            .all()
        )

        if not systems:
            print("[weather] no active systems with coordinates")
            return 0

        for system in systems:
            tz = system.timezone or "auto"
            try:
                current_params = {
                    "latitude": system.latitude,
                    "longitude": system.longitude,
                    "current": "shortwave_radiation,cloud_cover,temperature_2m",
                    "timezone": tz,
                }
                current_data = fetch_open_meteo(current_params)
                db.add(
                    WeatherCurrent(
                        system_id=system.system_id,
                        fetched_at=datetime.utcnow(),
                        data=current_data,
                    )
                )

                forecast_params = {
                    "latitude": system.latitude,
                    "longitude": system.longitude,
                    "hourly": "shortwave_radiation,cloud_cover,wind_speed_10m,temperature_2m",
                    "forecast_days": 1,
                    "timezone": tz,
                }
                forecast_data = fetch_open_meteo(forecast_params)
                db.add(
                    WeatherForecast(
                        system_id=system.system_id,
                        days=1,
                        fetched_at=datetime.utcnow(),
                        data=forecast_data,
                    )
                )

                db.commit()
                print(f"[weather] updated {system.system_id}")
            except Exception as exc:
                db.rollback()
                print(f"[weather] failed {system.system_id}: {exc}")

        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
