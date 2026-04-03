#!/usr/bin/env python3
"""
定时获取所有活跃系统的天气预报数据
每小时整点执行一次
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import SessionLocal
from app.services.weather_service import (
    create_retry_session,
    fetch_and_store_forecast,
    get_active_systems,
)


def fetch_forecast_for_system(db, system, session, days=1):
    """获取单个系统的预报数据"""
    try:
        fetch_and_store_forecast(db, system, days=days, session=session)
        
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
        systems = get_active_systems(db)
        
        if not systems:
            print("⚠️  没有找到活跃的系统")
            return
        
        print(f"📊 开始更新 {len(systems)} 个系统的预报数据...")
        print(f"⏰ 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        
        session = create_retry_session()
        success_count = 0
        for system in systems:
            if fetch_forecast_for_system(db, system, session, days=2):
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
