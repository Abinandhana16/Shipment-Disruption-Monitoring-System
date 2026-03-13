import os
import google.generativeai as genai
import json

def calculate_risk_score(weather: dict, traffic: dict, news: dict, priority: str) -> str:
    """Simple heuristic to calculate baseline risk category based on API severities."""
    severities = [weather['severity'], traffic['severity'], news['severity']]
    
    if 'High' in severities:
        return 'High'
    
    med_count = severities.count('Medium')
    if med_count >= 2:
        return 'High'
    elif med_count == 1:
        if priority.upper() == 'HIGH':
            return 'High'  # High priority shipments are sensitive to medium disruptions
        return 'Medium'
        
    return 'Low'

def analyze_shipment_risk(shipment, weather, traffic, news, live_risk):
    """
    Uses Google Gemini 1.5 Flash to predict risk and suggest actions.
    Should return a JSON object with keys:
    Explanation, PredictedDelay, RecommendedAction, AlternateRoute, DriverAlert
    """
    api_key = os.getenv("GEMINI_API_KEY")
    
    # Handle missing API key gracefully
    if not api_key:
        reasons = []
        if weather['severity'] in ['High', 'Medium']:
            reasons.append(weather['details'])
        if traffic['severity'] in ['High', 'Medium']:
            reasons.append(traffic['details'])
        if news['severity'] in ['High', 'Medium']:
            reasons.append(news['details'])
            
        if not reasons:
            explanation = "Conditions are clear, no major disruptions detected."
        else:
            import random
            explanation = "Risk signal detected: " + random.choice(reasons)
            
        return {
            "Explanation": explanation,
            "PredictedDelay": "1-2 hours" if live_risk == 'High' else ("30 mins" if live_risk == 'Medium' else "On time"),
            "RecommendedAction": "Reroute immediately" if live_risk == 'High' else "Monitor closely" if live_risk == 'Medium' else "Proceed normally",
            "AlternateRoute": f"Bypass regular route via state highway 4" if live_risk in ['High', 'Medium'] else "N/A",
            "DriverAlert": f"Alert: {live_risk} risk detected. {explanation}"
        }

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are an AI Logistics Expert. Analyze the following shipment disruption data and provide a recommended response.
        
        Shipment Details:
        - Origin: {shipment['origin']}
        - Destination: {shipment['destination']}
        - Priority: {shipment['priority']}
        - Current Risk Score: {live_risk}
        
        Disruption Signals:
        - Weather: {weather['details']} (Severity: {weather['severity']})
        - Traffic: {traffic['details']} (Severity: {traffic['severity']})
        - News: {news['details']} (Severity: {news['severity']})
        
        Output exclusively valid JSON with these keys:
        - Explanation: (A short explanation of the risk)
        - PredictedDelay: (Estimated delay time in hours or mins)
        - RecommendedAction: (What the manager should do)
        - AlternateRoute: (A brief description of a possible alternate route avoiding the core origin/destination bottleneck, or "N/A" if none needed)
        - DriverAlert: (A short message to send the driver)
        """
        
        response = model.generate_content(prompt)
        text = response.text
        
        # Clean markdown code block syntax if present
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        return result
        
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return {
            "Explanation": "AI Analysis unavailable due to API error.",
            "PredictedDelay": "Unknown",
            "RecommendedAction": "Proceed with caution.",
            "AlternateRoute": "N/A",
            "DriverAlert": "Drive safely, potential disruptions ahead."
        }
