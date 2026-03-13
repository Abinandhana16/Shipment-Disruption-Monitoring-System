import streamlit as st
import folium
from streamlit_folium import st_folium

from database import SessionLocal
import crud
from modules import ai_analysis, weather_api, traffic_api, news_api

st.set_page_config(page_title="Customer Dashboard", layout="wide", page_icon="📦")

st.markdown("""
<style>
    .stApp { background-color: #ffffff; color: #111827; }
    .header-box { text-align: center; font-size: 2.2rem; font-weight: 700; color: #1f2937; margin: 0; padding: 10px 0; }
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; max-width: 1200px; }
    .panel { border: 1px solid #bae6fd; border-radius: 8px; padding: 15px; background: #f0f9ff; margin-top: 10px; margin-bottom: 10px; }
    .alert-panel { background: #fef2f2; border-left: 5px solid #ef4444; border-radius: 8px; padding: 15px; color: #991b1b; font-weight: bold; margin-bottom: 15px; margin-top: 10px; }
    h1, h2, h3, h4, h5, p { margin-bottom: 4px !important; margin-top: 4px !important; }
    hr { margin-top: 0.5rem; margin-bottom: 0.5rem; border-top: 1px solid #e5e7eb; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='header-box'>Customer Shipment Tracking</div>", unsafe_allow_html=True)
st.markdown("<hr/>", unsafe_allow_html=True)

if st.button("⬅ Back to Role Selection"):
    st.switch_page("app.py")

db = SessionLocal()
all_shipments = crud.get_shipments(db)
shipments_ids = [s.shipment_id for s in all_shipments]

if not shipments_ids:
    st.info("No active shipments found.")
    st.stop()

col_login, _ = st.columns([1, 2])
with col_login:
    driver_shipment = st.selectbox("Select or Search Shipment ID", ["-- Select --"] + shipments_ids)

if driver_shipment != "-- Select --":
    shipment = next(s for s in all_shipments if s.shipment_id == driver_shipment)
    
    with st.spinner("Retrieving latest tracking data..."):
        weather = weather_api.get_weather_disruption(shipment.origin_lat, shipment.origin_lon, shipment.risk_score)
        traffic = traffic_api.get_traffic_disruption(shipment.origin_lat, shipment.origin_lon, shipment.risk_score)
        news = news_api.get_news_disruption(shipment.origin, shipment.risk_score)
        
        base_risk = ai_analysis.calculate_risk_score(weather, traffic, news, shipment.priority)
        if shipment.status == "EMERGENCY":
            base_risk = "High"

        s_dict = {"origin": shipment.origin, "destination": shipment.destination, "priority": shipment.priority}
        ai_res = ai_analysis.analyze_shipment_risk(s_dict, weather, traffic, news, base_risk)
        has_alt = ai_res.get("AlternateRoute") and ai_res.get("AlternateRoute") != "N/A"
        
        c_map, c_info = st.columns([3, 2])
        
        with c_map:
            st.markdown("**Live Tracking Map**", unsafe_allow_html=True)
            st.markdown("<div class='panel' style='padding:5px;'>", unsafe_allow_html=True)
            mid_lat = (shipment.origin_lat + shipment.destination_lat) / 2
            mid_lon = (shipment.origin_lon + shipment.destination_lon) / 2
            m = folium.Map(location=[mid_lat, mid_lon], zoom_start=6, tiles='CartoDB positron')
            
            folium.Marker([shipment.origin_lat, shipment.origin_lon], popup="Origin", icon=folium.Icon(color="green")).add_to(m)
            folium.Marker([shipment.destination_lat, shipment.destination_lon], popup="Destination", icon=folium.Icon(color="red")).add_to(m)
            
            route_color = "#ef4444" if base_risk == "High" else "#3b82f6"
            folium.PolyLine(
                [[shipment.origin_lat, shipment.origin_lon], [shipment.destination_lat, shipment.destination_lon]],
                color=route_color, weight=5, opacity=0.8
            ).add_to(m)
            
            if base_risk in ["High", "Medium"] and has_alt:
                alt_mid_lat = mid_lat + 0.8
                alt_mid_lon = mid_lon + 0.1
                folium.PolyLine(
                    [[shipment.origin_lat, shipment.origin_lon], [alt_mid_lat, alt_mid_lon], [shipment.destination_lat, shipment.destination_lon]],
                    color="#10b981", weight=4, opacity=0.9, dash_array='8', tooltip=f"Alternate: {ai_res.get('AlternateRoute')}"
                ).add_to(m)
            
            # Truck mock (30% through journey)
            t_lat = shipment.origin_lat + (shipment.destination_lat - shipment.origin_lat) * 0.3
            t_lon = shipment.origin_lon + (shipment.destination_lon - shipment.origin_lon) * 0.3
            folium.Marker([t_lat, t_lon], tooltip="Your Shipment", icon=folium.Icon(icon="truck", prefix="fa", color="blue")).add_to(m)
            
            st_folium(m, use_container_width=True, height=350, returned_objects=[])
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c_info:
            st.markdown("**Shipment Details & Status**", unsafe_allow_html=True)
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown(f"**Origin:** {shipment.origin}")
            st.markdown(f"**Destination:** {shipment.destination}")
            
            status_color = "#10b981" if shipment.status == "PENDING" or shipment.status == "DELIVERED" else "#ef4444"
            st.markdown(f"**Network Status:** <span style='color:{status_color}; font-weight:bold;'>{shipment.status}</span>", unsafe_allow_html=True)
            st.markdown(f"**Risk Level:** {base_risk}")
            
            eta = ai_res.get('PredictedDelay', 'Unknown')
            if 'none' in eta.lower() or 'on time' in eta.lower():
                eta = "On Time (Approx. ETA 24-48 Business Hours)"
            else:
                eta = f"Delayed by {eta}"
            
            st.markdown(f"**Expected Delivery Time / Delay:** {eta}")
            
            st.markdown("<div style='margin-top: 15px; padding-top: 15px; border-top: 1px solid #e5e7eb;'>", unsafe_allow_html=True)
            st.markdown("**AI Logistic Analysis Info:**")
            st.markdown(ai_res.get('Explanation', 'No issues detected on this route.'))
            st.markdown("</div>", unsafe_allow_html=True)
            
            if base_risk == "High" or shipment.status == "EMERGENCY":
                st.markdown("<div class='alert-panel'>🚨 **DELAY NOTIFICATION:** Your shipment is delayed due to unexpected conditions. The driver has been notified of alternate routing.</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

db.close()
