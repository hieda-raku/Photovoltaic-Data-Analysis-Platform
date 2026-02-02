"""
光伏数据分析平台 API 的示例用法脚本。

该脚本演示如何使用 Python requests 与 API 交互。
注意：需要启动 API 服务器并配置 PostgreSQL 数据库。
"""

# 示例导入（需要先执行：pip install requests）
# import requests
# import json
# from datetime import datetime

# API 基础地址
BASE_URL = "http://localhost:8000"

# 示例 1：创建系统配置
example_system = {
    "system_id": "PV-001",
    "name": "Rooftop Solar Array - Building A",
    "capacity": 10.0,
    "panel_count": 40,
    "panel_wattage": 250.0,
    "inverter_model": "SolarEdge SE10000H",
    "location": "Main Campus, Building A",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "tilt_angle": 30.0,
    "azimuth": 180.0,
    "is_active": True
}

# 发送 POST 请求创建系统配置
# response = requests.post(f"{BASE_URL}/systems/", json=example_system)
# print(f"System created: {response.json()}")

# 示例 2：写入单条测量数据
example_measurement = {
    "system_id": "PV-001",
    "irradiance": 850.0,
    "temperature": 35.2,
    "ambient_temperature": 25.0
}

# 发送 POST 请求创建测量记录
# response = requests.post(f"{BASE_URL}/measurements/", json=example_measurement)
# print(f"Measurement created: {response.json()}")

# 示例 3：批量写入测量数据
example_batch = {
    "measurements": [
        {
            "system_id": "PV-001",
            "irradiance": 850.0,
            "temperature": 35.2
        },
        {
            "system_id": "PV-001",
            "irradiance": 870.0,
            "temperature": 34.8
        },
        {
            "system_id": "PV-001",
            "irradiance": 830.0,
            "temperature": 35.5
        }
    ]
}

# 发送批量写入的 POST 请求
# response = requests.post(f"{BASE_URL}/measurements/batch", json=example_batch)
# print(f"Batch created: {len(response.json())} measurements")

# 示例 4：查询测量数据
# 获取指定系统的最近测量记录
# params = {
#     "system_id": "PV-001",
#     "limit": 10
# }
# response = requests.get(f"{BASE_URL}/measurements/", params=params)
# measurements = response.json()
# print(f"Retrieved {len(measurements)} measurements")

# 示例 5：获取系统配置
# response = requests.get(f"{BASE_URL}/systems/PV-001")
# system = response.json()
# print(f"System: {system['name']} - {system['capacity']}kW")

# 示例 6：更新系统配置
# update_data = {
#     "is_active": False
# }
# response = requests.put(f"{BASE_URL}/systems/PV-001", json=update_data)
# print(f"System updated: {response.json()}")

# 示例 7：直接使用计算模块（无需调用 API）
from app.calculations import calculate_efficiency, estimate_daily_energy, PVCalculator

# 计算效率
power = 596.55  # W
irradiance = 850.0  # W/m²
area = 25.0  # m²
efficiency = calculate_efficiency(power, irradiance, area)
print(f"Efficiency: {efficiency}%")

# 估算日发电量
capacity_kw = 10.0
peak_sun_hours = 5.0
daily_energy = estimate_daily_energy(capacity_kw, peak_sun_hours)
print(f"Estimated daily energy: {daily_energy}kWh")

# 计算性能比
actual = 8500
theoretical = 10000
pr = PVCalculator.calculate_performance_ratio(actual, theoretical)
print(f"Performance ratio: {pr}%")

print("\nTo run this API example, start the server with:")
print("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")
print("\nThen uncomment the API call examples above and run this script.")
