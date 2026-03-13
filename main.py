from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import models, schemas, crud
from database import SessionLocal, engine, Base
import os

# Create DB schema
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print("DB Init Error:", e)

app = FastAPI(title="Logistics Monitoring API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/update_location", tags=["Driver API"])
def update_location(location: schemas.LocationUpdate, db: Session = Depends(get_db)):
    """Receives live GPS updates from Driver device."""
    crud.update_truck_location(db, location)
    return {"status": "success", "message": "Location updated."}

@app.get("/locations", tags=["Dashboard API"])
def get_live_locations(db: Session = Depends(get_db)):
    """Returns live locations of all active trucks/drivers."""
    drivers = crud.get_truck_locations(db)
    res = []
    for d in drivers:
        res.append({
            "driver_id": d.driver_id,
            "truck_id": d.truck_id,
            "latitude": d.current_lat,
            "longitude": d.current_lon
        })
    return res

@app.post("/upload_shipments", tags=["Dashboard API"])
def upload_shipments(shipments: List[schemas.ShipmentCreate], db: Session = Depends(get_db)):
    """Bulk imports shipments into DB."""
    crud.load_shipments_bulk(db, shipments)
    return {"status": "success"}

@app.get("/shipments", tags=["Dashboard API"])
def get_shipments(db: Session = Depends(get_db)):
    """Gets all shipments."""
    ships = crud.get_shipments(db)
    return ships

@app.get("/driver", response_class=HTMLResponse, tags=["Driver Interface"])
def driver_interface():
    """Serves the Driver Web Interface."""
    path = os.path.join(os.path.dirname(__file__), "driver_ui.html")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"<html><body><h2>Error loading Driver UI: {e}</h2></body></html>"
