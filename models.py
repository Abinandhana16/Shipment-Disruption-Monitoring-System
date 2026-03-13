from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime
from database import Base

class Driver(Base):
    __tablename__ = "drivers"
    driver_id = Column(String(50), primary_key=True, index=True)
    driver_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    truck_id = Column(String(50), ForeignKey("trucks.truck_id"))
    status = Column(String(50), default="AVAILABLE")
    current_lat = Column(Float, nullable=True)
    current_lon = Column(Float, nullable=True)

    truck = relationship("Truck", back_populates="drivers")


class Truck(Base):
    __tablename__ = "trucks"
    truck_id = Column(String(50), primary_key=True, index=True)
    truck_number = Column(String(50), unique=True, nullable=False)
    capacity = Column(Float)
    status = Column(String(50), default="IDLE") # IDLE, ON_ROUTE, MAINTENANCE
    driver_id = Column(String(50), nullable=True)

    drivers = relationship("Driver", back_populates="truck")


class Shipment(Base):
    __tablename__ = "shipments"
    shipment_id = Column(String(50), primary_key=True, index=True)
    origin = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    origin_lat = Column(Float, nullable=False)
    origin_lon = Column(Float, nullable=False)
    destination_lat = Column(Float, nullable=False)
    destination_lon = Column(Float, nullable=False)
    priority = Column(String(50), default="LOW")
    customer_phone = Column(String(20), nullable=False)
    customer_email = Column(String(100), nullable=True)
    status = Column(String(50), default="PENDING")
    assigned_truck = Column(String(50), ForeignKey("trucks.truck_id"), nullable=True)
    risk_score = Column(String(50), default="LOW")


class RouteTracking(Base):
    __tablename__ = "route_tracking"
    tracking_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    truck_id = Column(String(50), ForeignKey("trucks.truck_id"), index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True)
    password = Column(String(255))
    role = Column(String(50)) # Company, Driver, Customer
    email = Column(String(100), nullable=True)
