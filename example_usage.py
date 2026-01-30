"""
Example usage script for the Photovoltaic Data Analysis Platform API.

This script demonstrates how to interact with the API using Python requests.
Note: Requires the API server to be running and a PostgreSQL database.
"""

# Example imports (would need: pip install requests)
# import requests
# import json
# from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8000"

# Example 1: Create a system configuration
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

# POST request to create system
# response = requests.post(f"{BASE_URL}/systems/", json=example_system)
# print(f"System created: {response.json()}")

# Example 2: Ingest a single measurement
example_measurement = {
    "system_id": "PV-001",
    "voltage": 48.5,
    "current": 12.3,
    "power": 596.55,
    "irradiance": 850.0,
    "temperature": 35.2,
    "ambient_temperature": 25.0
}

# POST request to create measurement
# response = requests.post(f"{BASE_URL}/measurements/", json=example_measurement)
# print(f"Measurement created: {response.json()}")

# Example 3: Ingest multiple measurements in batch
example_batch = {
    "measurements": [
        {
            "system_id": "PV-001",
            "power": 596.55,
            "irradiance": 850.0,
            "temperature": 35.2
        },
        {
            "system_id": "PV-001",
            "power": 610.25,
            "irradiance": 870.0,
            "temperature": 34.8
        },
        {
            "system_id": "PV-001",
            "power": 582.30,
            "irradiance": 830.0,
            "temperature": 35.5
        }
    ]
}

# POST request for batch ingestion
# response = requests.post(f"{BASE_URL}/measurements/batch", json=example_batch)
# print(f"Batch created: {len(response.json())} measurements")

# Example 4: Query measurements
# Get recent measurements for a specific system
# params = {
#     "system_id": "PV-001",
#     "limit": 10
# }
# response = requests.get(f"{BASE_URL}/measurements/", params=params)
# measurements = response.json()
# print(f"Retrieved {len(measurements)} measurements")

# Example 5: Get system configuration
# response = requests.get(f"{BASE_URL}/systems/PV-001")
# system = response.json()
# print(f"System: {system['name']} - {system['capacity']}kW")

# Example 6: Update system configuration
# update_data = {
#     "is_active": False
# }
# response = requests.put(f"{BASE_URL}/systems/PV-001", json=update_data)
# print(f"System updated: {response.json()}")

# Example 7: Using the calculation module directly (no API call needed)
from app.calculations import calculate_efficiency, estimate_daily_energy, PVCalculator

# Calculate efficiency
power = 596.55  # W
irradiance = 850.0  # W/m²
area = 25.0  # m²
efficiency = calculate_efficiency(power, irradiance, area)
print(f"Efficiency: {efficiency}%")

# Estimate daily energy
capacity_kw = 10.0
peak_sun_hours = 5.0
daily_energy = estimate_daily_energy(capacity_kw, peak_sun_hours)
print(f"Estimated daily energy: {daily_energy}kWh")

# Calculate performance ratio
actual = 8500
theoretical = 10000
pr = PVCalculator.calculate_performance_ratio(actual, theoretical)
print(f"Performance ratio: {pr}%")

print("\nTo run this API example, start the server with:")
print("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")
print("\nThen uncomment the API call examples above and run this script.")
