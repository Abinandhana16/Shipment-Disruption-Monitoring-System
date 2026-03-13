from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LocationUpdate(BaseModel):
    truck_id: str
    latitude: float
    longitude: float

class LocationResponse(BaseModel):
    status: str
    
class DriverLogin(BaseModel):
    driver_id: str
    
class ShipmentCreate(BaseModel):
    shipment_id: str
    origin: str
    destination: str
    origin_lat: float
    origin_lon: float
    destination_lat: float
    destination_lon: float
    priority: str
    customer_phone: str
    customer_email: Optional[str] = None
    status: Optional[str] = "PENDING"
    assigned_truck: Optional[str] = None
    risk_score: Optional[str] = "LOW"

class TrackingOut(BaseModel):
    truck_id: str
    latitude: float
    longitude: float
    timestamp: datetime
    
    class Config:
        from_attributes = True
