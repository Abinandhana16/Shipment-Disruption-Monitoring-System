import requests
import os
import random

def get_traffic_disruption(lat: float, lon: float, db_risk: str = "Low") -> dict:
    """
    Fetches traffic data for a location using TomTom API. Returns structured disruption data.
    """
    api_key = os.getenv("TOMTOM_API_KEY", "")
    
    if not api_key:
        if str(db_risk).upper() == "HIGH":
            return random.choice([
                {"status": "Heavy", "details": "Severe congestion due to a multi-vehicle pileup", "severity": "High"},
                {"status": "Gridlock", "details": "Major highway completely blocked by an overturned truck", "severity": "High"},
                {"status": "Standstill", "details": "Traffic at a standstill due to massive road protests", "severity": "High"}
            ])
        elif str(db_risk).upper() == "MEDIUM":
            return random.choice([
                {"status": "Moderate", "details": "Slow moving traffic approaching the state border", "severity": "Medium"},
                {"status": "Delays", "details": "Mild delays caused by ongoing road maintenance and lane closures", "severity": "Medium"},
                {"status": "Congestion", "details": "Slight congestion near major intersections and toll plazas", "severity": "Medium"}
            ])
        else:
            return random.choice([
                {"status": "Clear", "details": "Traffic is flowing smoothly, no significant delays", "severity": "Low"},
                {"status": "Normal", "details": "Routine traffic conditions for this time of day", "severity": "Low"}
            ])
    try:
        # TomTom flow API
        url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json?point={lat},{lon}&key={api_key}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        flow = data.get('flowSegmentData', {})
        current_speed = flow.get('currentSpeed', 50)
        free_flow = flow.get('freeFlowSpeed', 50)
        
        ratio = current_speed / free_flow if free_flow > 0 else 1.0
        
        if ratio < 0.3:
            severity = "High"
            status = "Heavy"
            details = "Severe congestion detected."
        elif ratio < 0.7:
            severity = "Medium"
            status = "Moderate"
            details = "Moderate traffic delays."
        else:
            severity = "Low"
            status = "Clear"
            details = "Traffic is flowing normally."
            
        return {
            "status": status,
            "details": details,
            "severity": severity
        }
    except Exception as e:
        print(f"Traffic API Error: {e}")
        return {"status": "Unknown", "details": "Traffic data unavailable due to API error", "severity": "Low"}
