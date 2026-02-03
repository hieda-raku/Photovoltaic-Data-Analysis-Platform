#!/usr/bin/env python3
"""
批量更新系统配置的地点名称

用途：为所有有经纬度但缺少 location_name 的系统补充地点信息
运行：python scripts/update_location_names.py
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.system_config import SystemConfiguration


def get_location_name(lat, lon):
    """
    通过高德地图 API 获取坐标对应的地点名称（精确到街道级别）
    """
    amap_key = os.getenv('AMAP_KEY')
    if not amap_key:
        print("  ⚠️  未配置 AMAP_KEY 环境变量")
        return None
    
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(
                'https://restapi.amap.com/v3/geocode/regeo',
                params={
                    'location': f'{lon},{lat}',
                    'key': amap_key
                }
            )
            data = response.json()
            if data.get('status') == '1' and data.get('regeocode'):
                addr_comp = data['regeocode'].get('addressComponent', {})
                province = addr_comp.get('province', '')
                city = addr_comp.get('city', '')
                if isinstance(city, list):
                    city = ''
                district = addr_comp.get('district', '')
                township = addr_comp.get('township', '')
                
                # 组合到街道级别
                parts = [province, city, district, township]
                return ''.join(filter(None, parts))
    except Exception as e:
        print(f"  ⚠️  获取失败: {e}")
    
    return None


def main():
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/photovoltaic_db')
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    
    db = SessionLocal()
    try:
        # 查找所有有经纬度但没有 location_name 的系统
        systems = db.query(SystemConfiguration).filter(
            SystemConfiguration.latitude.isnot(None),
            SystemConfiguration.longitude.isnot(None),
            SystemConfiguration.location_name.is_(None)
        ).all()
        
        print(f"找到 {len(systems)} 个需要更新的系统:\n")
        
        updated_count = 0
        for system in systems:
            print(f"🔄 更新 {system.system_id}...")
            location_name = get_location_name(system.latitude, system.longitude)
            if location_name:
                system.location_name = location_name
                print(f"  ✅ {location_name}")
                updated_count += 1
            else:
                print(f"  ❌ 无法获取地点名称")
        
        if updated_count > 0:
            db.commit()
            print(f"\n✅ 成功更新 {updated_count} 个系统的地点名称！")
        else:
            print(f"\n⚠️  没有系统需要更新")
        
    finally:
        db.close()


if __name__ == '__main__':
    main()
