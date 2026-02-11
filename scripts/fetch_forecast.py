#!/usr/bin/env python3
"""
定时获取所有活跃系统的天气预报数据
每小时整点执行一次
"""
import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import SessionLocal
from app.models.system_config import SystemConfiguration
from app.models.weather import WeatherForecast
import requests

OPEN_METEO_API_URL = "https://api.open-meteo.com/v1/forecast"

SYSTEM_TIMEZONE = "Asia/Shanghai"


def _get_local_now() -> datetime:
    return datetime.now(ZoneInfo(SYSTEM_TIMEZONE)).replace(tzinfo=None)


def fetch_forecast_for_system(db, system, days=1):
    """获取单个系统的预报数据"""
    try:
        params = {
            "latitude": system.latitude,
            "longitude": system.longitude,
            "hourly": "shortwave_radiation,cloud_cover,temperature_2m,wind_speed_10m",
            "timezone": system.timezone or "auto",
            "forecast_days": days,
            "wind_speed_unit": "ms",
        }
        
        response = requests.get(OPEN_METEO_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # 存入数据库
        now = _get_local_now()
        record = WeatherForecast(
            system_id=system.system_id,
            days=days,
            fetched_at=now,
            created_at=now,
            data=data,
        )
        db.add(record)
        db.commit()
        
        print(f"✅ {system.system_id} ({system.name}): 预报数据已更新")
        return True
        
    except Exception as e:
        print(f"❌ {system.system_id} ({system.name}): 更新失败 - {e}")
        return False


def main():
    """主函数：批量更新所有活跃系统的预报数据"""
    db = SessionLocal()
    
    try:
        # 获取所有活跃系统
        systems = (
            db.query(SystemConfiguration)
            .filter(SystemConfiguration.is_active == True)
            .all()
        )
        
        if not systems:
            print("⚠️  没有找到活跃的系统")
            return
        
        print(f"📊 开始更新 {len(systems)} 个系统的预报数据...")
        print(f"⏰ 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        
        success_count = 0
        for system in systems:
            if fetch_forecast_for_system(db, system, days=2):
                success_count += 1
        
        print("-" * 60)
        print(f"✨ 完成！成功: {success_count}/{len(systems)}")
        
    except Exception as e:
        print(f"❌ 批量更新失败: {e}")
        sys.exit(1)
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
