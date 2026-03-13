import streamlit as st
import folium
from streamlit_folium import st_folium
import os
import random

from database import SessionLocal
import crud
from modules import ai_analysis, weather_api, traffic_api, news_api, email_service

st.set_page_config(page_title="Driver Dashboard", layout="wide", page_icon="🚛")

# Clean white theme overrides
st.markdown("""
<style>
    .stApp { background-color: #ffffff; color: #111827; }
    .header-box { text-align: center; font-size: 2.2rem; font-weight: 700; color: #1f2937; margin: 0; padding: 10px 0; }
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; max-width: 1400px; }
    .stSelectbox div[data-baseweb="select"] { border: 1px solid #d1d5db !important; background-color: #ffffff !important; color: #000 !important; }
    .panel { border: 1px solid #bae6fd; border-radius: 8px; padding: 15px; background: #f0f9ff; margin-top: 10px; margin-bottom: 10px; }
    .alert-panel { background: #fef2f2; border-left: 5px solid #ef4444; border-radius: 8px; padding: 15px; color: #991b1b; font-weight: bold; margin-bottom: 15px; margin-top: 10px; }
    
    h1, h2, h3, h4, h5, p { margin-bottom: 4px !important; margin-top: 4px !important; }
    hr { margin-top: 0.5rem; margin-bottom: 0.5rem; border-top: 1px solid #e5e7eb; }
    
    .stButton>button { width: 100%; border-radius: 8px; padding: 15px; font-weight: bold; font-size: 1.1rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='header-box'>Driver Dashboard</div>", unsafe_allow_html=True)
st.markdown("<hr/>", unsafe_allow_html=True)

if st.button("⬅ Back to Role Selection"):
    st.switch_page("app.py")

db = SessionLocal()
all_shipments = crud.get_shipments(db)
shipments_ids = [s.shipment_id for s in all_shipments]

if not shipments_ids:
    st.info("No active shipments available.")
    st.stop()

col_login, _ = st.columns([1, 2])
with col_login:
    driver_shipment = st.selectbox("Select Shipment ID", ["-- Select --"] + shipments_ids)

if driver_shipment != "-- Select --":
    shipment = next(s for s in all_shipments if s.shipment_id == driver_shipment)
    if st.session_state.get('driver_last_analyzed') != driver_shipment:
        st.session_state['driver_auto_alert_sent'] = set()
        st.session_state['driver_last_analyzed'] = driver_shipment

    with st.spinner("Connecting to Dispatch & Analyzing Route..."):
        weather = weather_api.get_weather_disruption(shipment.origin_lat, shipment.origin_lon, shipment.risk_score)
        traffic = traffic_api.get_traffic_disruption(shipment.origin_lat, shipment.origin_lon, shipment.risk_score)
        news = news_api.get_news_disruption(shipment.origin, shipment.risk_score)
        base_risk = ai_analysis.calculate_risk_score(weather, traffic, news, shipment.priority)
        
        # Merge if EMERGENCY
        if shipment.status == "EMERGENCY":
            base_risk = "High"

        s_dict = {"origin": shipment.origin, "destination": shipment.destination, "priority": shipment.priority}
        ai_res = ai_analysis.analyze_shipment_risk(s_dict, weather, traffic, news, base_risk)
        has_alt = ai_res.get("AlternateRoute") and ai_res.get("AlternateRoute") != "N/A"
        
        c_map, c_info = st.columns([3, 2])
        
        with c_map:
            st.markdown("**Route Map**")
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
            
            st_folium(m, use_container_width=True, height=350, returned_objects=[])
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c_info:
            st.markdown("**Risk Status & AI Analysis**")
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            if base_risk == "High":
                st.markdown("<div class='alert-panel'>ALERT: Route changed due to disruption. Please follow the alternate path.</div>", unsafe_allow_html=True)
                
                if driver_shipment not in st.session_state.get('driver_auto_alert_sent', set()):
                    # Play Alert Sound
                    import base64
                    if os.path.exists("alert.wav"):
                        with open("alert.wav", "rb") as f:
                            b64 = base64.b64encode(f.read()).decode()
                            st.markdown(f'<audio autoplay="true" style="display:none;"><source src="data:audio/wav;base64,{b64}" type="audio/wav"></audio>', unsafe_allow_html=True)

                    # Send Email Alert
                    email = shipment.customer_email
                    if email and "@" in email:
                        email_service.send_reroute_email(email, shipment.shipment_id)
                    
                    if 'driver_auto_alert_sent' not in st.session_state:
                        st.session_state['driver_auto_alert_sent'] = set()
                    st.session_state['driver_auto_alert_sent'].add(driver_shipment)
                    # Use a transient success message only when it triggers
                    st.toast("Emergency notifications and alerts triggered successfully.", icon="🚨")
                
            st.markdown(f"**Risk Level:** <span style='color:{'#ef4444' if base_risk=='High' else '#f59e0b' if base_risk=='Medium' else '#10b981'};'>{base_risk}</span>", unsafe_allow_html=True)
            st.markdown(f"**Analysis:** {ai_res.get('Explanation', 'No issues detected.')}")
            
            if base_risk == "High" and has_alt:
                st.markdown(f"**Alternate Route:** <span style='color:#10b981;'>{ai_res.get('AlternateRoute')}</span>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<hr/>", unsafe_allow_html=True)
            st.markdown("**Emergency Action Panel**")
            
            def report_issue(issue_type):
                shipment.status = "EMERGENCY"
                db.commit()
                email = shipment.customer_email
                if email and "@" in email:
                    email_service.send_driver_emergency_email(email, issue_type)
                st.success("Successfully sent notification.")
            
            st.button("🔴 Report Tire Puncture", on_click=report_issue, args=("Tire Puncture",))
            st.button("🔴 Report Breakdown", on_click=report_issue, args=("Vehicle Breakdown",))
            st.button("🔴 Report Road Block", on_click=report_issue, args=("Road Block",))

db.close()
