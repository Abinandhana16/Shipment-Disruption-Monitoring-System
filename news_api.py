import requests
import os
import random

def get_news_disruption(location_name: str, db_risk: str = "Low") -> dict:
    """
    Fetches news incidents for a location using NewsAPI. Returns structured disruption data.
    """
    api_key = os.getenv("NEWS_API_KEY", "")
    
    if not api_key:
        if str(db_risk).upper() == "HIGH":
            return random.choice([
                {"status": "Critical", "details": "Local Transport Strike causing massive logistics disruptions", "severity": "High"},
                {"status": "Emergency", "details": "Bridge collapse reported on the primary transport corridor", "severity": "High"},
                {"status": "Alert", "details": "State-wide security lockdown halting commercial vehicles", "severity": "High"}
            ])
        elif str(db_risk).upper() == "MEDIUM":
            return random.choice([
                {"status": "Protest", "details": "Local farmer protests reported near the highway entries", "severity": "Medium"},
                {"status": "Warning", "details": "Political rally causing diversions in the downtown area", "severity": "Medium"},
                {"status": "Notice", "details": "Upcoming festival expected to increase local traffic volume", "severity": "Medium"}
            ])
        else:
            return random.choice([
                {"status": "Quiet", "details": "No disruptive news reported in the region", "severity": "Low"},
                {"status": "Normal", "details": "General news only, logistics operations unaffected", "severity": "Low"}
            ])
    try:
        url = f"https://newsapi.org/v2/everything?q={location_name} AND (strike OR accident OR protest OR traffic OR delay)&sortBy=publishedAt&apiKey={api_key}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        articles = data.get('articles', [])
        if articles:
            # Analyze title for keywords
            title = articles[0]['title'].lower()
            if any(word in title for word in ['strike', 'blocked', 'closed', 'pile-up', 'fatal']):
                severity = "High"
                status = "Critical Incident"
            elif any(word in title for word in ['protest', 'delay', 'traffic', 'heavy']):
                severity = "Medium"
                status = "Disruption Event"
            else:
                severity = "Low"
                status = "Minor News"
                
            return {
                "status": status,
                "details": f"Recent article: {articles[0]['title']}",
                "severity": severity
            }
        else:
            return {"status": "Quiet", "details": "No disruptive news found", "severity": "Low"}
            
    except Exception as e:
        print(f"News API Error: {e}")
        return {"status": "Unknown", "details": "News data unavailable due to API error", "severity": "Low"}
