import requests
import os
import random

def get_weather_disruption(lat: float, lon: float, db_risk: str = "Low") -> dict:
    """
    Fetches weather data for a location. Returns structured disruption data.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY", "")
    
    if not api_key:
        if str(db_risk).upper() == "HIGH":
            return random.choice([
                {"status": "Storm", "details": "Severe thunderstorm with lightning", "severity": "High"},
                {"status": "Cyclone", "details": "Cyclone alert issued for the coastal region", "severity": "High"},
                {"status": "Floods", "details": "Sudden flash floods submerging state highways", "severity": "High"}
            ])
        elif str(db_risk).upper() == "MEDIUM":
            return random.choice([
                {"status": "Rain", "details": "Heavy rainfall expected to reduce visibility", "severity": "Medium"},
                {"status": "Fog", "details": "Dense fog causing hazardous driving conditions", "severity": "Medium"},
                {"status": "Wind", "details": "Strong crosswinds impacting high-profile vehicles", "severity": "Medium"}
            ])
        else:
            return random.choice([
                {"status": "Clear", "details": "Clear skies, no disruption", "severity": "Low"},
                {"status": "Cloudy", "details": "Partly cloudy, safe driving conditions", "severity": "Low"}
            ])
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        main_weather = data['weather'][0]['main']
        desc = data['weather'][0]['description']
        
        severity = "Low"
        if main_weather in ["Thunderstorm", "Tornado", "Snow", "Extreme"]:
            severity = "High"
        elif main_weather in ["Rain", "Drizzle", "Fog", "Mist"]:
            severity = "Medium"
            
        return {
            "status": main_weather,
            "details": f"{desc.capitalize()}",
            "severity": severity
        }
    except Exception as e:
        print(f"Weather API Error: {e}")
        return {"status": "Unknown", "details": "Weather data unavailable due to API error", "severity": "Low"}
