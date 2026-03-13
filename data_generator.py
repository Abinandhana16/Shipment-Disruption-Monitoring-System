import pandas as pd
import random
import os

# Create datasets directory
if not os.path.exists("datasets"):
    os.makedirs("datasets")

cities = [
    {"city": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"city": "Delhi", "lat": 28.7041, "lon": 77.1025},
    {"city": "Bangalore", "lat": 12.9716, "lon": 77.5946},
    {"city": "Hyderabad", "lat": 17.3850, "lon": 78.4867},
    {"city": "Chennai", "lat": 13.0827, "lon": 80.2707},
    {"city": "Kolkata", "lat": 22.5726, "lon": 88.3639},
    {"city": "Pune", "lat": 18.5204, "lon": 73.8567},
    {"city": "Ahmedabad", "lat": 23.0225, "lon": 72.5714},
    {"city": "Jaipur", "lat": 26.9124, "lon": 75.7873},
    {"city": "Surat", "lat": 21.1702, "lon": 72.8311},
    {"city": "Vellore", "lat": 12.9165, "lon": 79.1325},
    {"city": "Krishnagiri", "lat": 12.5186, "lon": 78.2137},
]

drivers = [
    "Rajesh Kumar", "Amit Singh", "Suresh Patel", "Vikram Reddy", 
    "Mohammed Ali", "Ramesh Rao", "Karthik N", "Prakash C",
    "Deepak Sharma", "Arun M"
]

def generate_day_dataset(day, count=15):
    data = []
    for i in range(1, count + 1):
        origin = random.choice(cities)
        destination = random.choice([c for c in cities if c["city"] != origin["city"]])
        priority = random.choice(["Low", "Medium", "High"])
        driver = random.choice(drivers)
        # Random Indian phone numbers for customer_phone mock
        customer_phone = f"+91{random.randint(6000000000, 9999999999)}"
        
        data.append({
            "shipment_id": f"D{day}S{i:03d}",
            "origin": origin["city"],
            "destination": destination["city"],
            "origin_lat": origin["lat"] + random.uniform(-0.05, 0.05),
            "origin_lon": origin["lon"] + random.uniform(-0.05, 0.05),
            "destination_lat": destination["lat"] + random.uniform(-0.05, 0.05),
            "destination_lon": destination["lon"] + random.uniform(-0.05, 0.05),
            "priority": priority,
            "driver_name": driver,
            "customer_phone": customer_phone,
            "driver_alert_status": "Ok",
            "risk_score": random.choices(["Low", "Medium", "High"], weights=[0.6, 0.25, 0.15])[0]
        })

    df = pd.DataFrame(data)
    filepath = f"datasets/shipments_day{day}.csv"
    df.to_csv(filepath, index=False)
    print(f"{filepath} created successfully.")

for day in range(1, 4):
    generate_day_dataset(day, count=25)
