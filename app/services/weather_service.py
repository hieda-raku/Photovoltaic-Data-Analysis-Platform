from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from sqlalchemy.orm import Session
from urllib3.util.retry import Retry

from app.models.system_config import SystemConfiguration
from app.models.weather import WeatherCurrent, WeatherForecast
from app.utils.time_utils import local_now_naive

OPEN_METEO_API_URL = "https://api.open-meteo.com/v1/forecast"


def create_retry_session() -> requests.Session:
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=0.8,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET"]),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": "pv-weather-fetcher/1.0"})
    return session


def get_system_by_id(db: Session, system_id: str) -> Optional[SystemConfiguration]:
    return (
        db.query(SystemConfiguration)
        .filter(SystemConfiguration.system_id == system_id)
        .first()
    )


def get_active_systems(db: Session):
    return (
        db.query(SystemConfiguration)
        .filter(SystemConfiguration.is_active == True)
        .all()
    )


def _fetch_open_meteo(params: dict, session: Optional[requests.Session] = None) -> dict:
    client = session or create_retry_session()
    response = client.get(OPEN_METEO_API_URL, params=params, timeout=(5, 20))
    response.raise_for_status()
    return response.json()


def fetch_and_store_current(
    db: Session,
    system: SystemConfiguration,
    session: Optional[requests.Session] = None,
) -> WeatherCurrent:
    params = {
        "latitude": system.latitude,
        "longitude": system.longitude,
        "current": "shortwave_radiation,cloud_cover,temperature_2m,wind_speed_10m",
        "timezone": system.timezone or "auto",
        "wind_speed_unit": "ms",
    }
    data = _fetch_open_meteo(params, session=session)

    now = local_now_naive()
    record = WeatherCurrent(
        system_id=system.system_id,
        fetched_at=now,
        created_at=now,
        data=data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def fetch_and_store_forecast(
    db: Session,
    system: SystemConfiguration,
    days: int = 1,
    session: Optional[requests.Session] = None,
) -> WeatherForecast:
    params = {
        "latitude": system.latitude,
        "longitude": system.longitude,
        "hourly": "shortwave_radiation,cloud_cover,temperature_2m,wind_speed_10m",
        "timezone": system.timezone or "auto",
        "forecast_days": days,
        "wind_speed_unit": "ms",
    }
    data = _fetch_open_meteo(params, session=session)

    now = local_now_naive()
    record = WeatherForecast(
        system_id=system.system_id,
        days=days,
        fetched_at=now,
        created_at=now,
        data=data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
