import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime
import base64
import random
import os

from database import SessionLocal
import models
import crud
from modules import weather_api, traffic_api, news_api, ai_analysis, notification_service, email_service

st.set_page_config(page_title="Company Dashboard", layout="wide", page_icon="🏢")

# Layout improvements: White theme, strict margins, remove whitespaces
st.markdown("""
<style>
    .stApp { background-color: #ffffff; color: #111827; }
    .header-box { text-align: center; font-size: 2.2rem; font-weight: 700; color: #1f2937; margin: 0; padding: 10px 0; }
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; max-width: 1400px; }
    .stSelectbox div[data-baseweb="select"] { border: 1px solid #d1d5db !important; background-color: #ffffff !important; color: #000 !important; }
    .panel { border: 1px solid #bae6fd; border-radius: 8px; padding: 10px; background: #f0f9ff; margin-top: 10px; margin-bottom: 10px; }
    .alert-panel { background: #fef2f2; border-left: 5px solid #ef4444; border-radius: 8px; padding: 15px; color: #991b1b; font-weight: bold; margin-bottom: 15px; margin-top: 10px; }
    
    h1, h2, h3, h4, h5, p { margin-bottom: 4px !important; margin-top: 4px !important; }
    hr { margin-top: 0.5rem; margin-bottom: 0.5rem; border-top: 1px solid #e5e7eb; }
</style>
""", unsafe_allow_html=True)

if 'alert_sent' not in st.session_state:
    st.session_state['alert_sent'] = set()
if 'email_sent' not in st.session_state:
    st.session_state['email_sent'] = set()

st.markdown("<div class='header-box'>AI Logistics Risk Monitoring Dashboard</div>", unsafe_allow_html=True)
st.markdown("<hr/>", unsafe_allow_html=True)

if st.button("⬅ Back to Role Selection"):
    st.switch_page("app.py")

db = SessionLocal()

def load_data(df_upload):
    if 'status' not in df_upload.columns:
        df_upload['status'] = 'PENDING'
    if 'risk_score' not in df_upload.columns:
        df_upload['risk_score'] = 'LOW'
        
    shipments_to_load = []
    import schemas
    for _, row in df_upload.iterrows():
        try:
            s_id = str(row.get('shipment_id', f"S-{random.randint(1000,9999)}"))
            # ensure customer_email exists
            c_email = str(row.get('customer_email', f"customer_{random.randint(10,99)}@example.com"))
            s = schemas.ShipmentCreate(
                shipment_id=s_id,
                origin=str(row['origin']),
                destination=str(row['destination']),
                origin_lat=float(row.get('origin_lat', row.get('origin_latitude', 0.0))),
                origin_lon=float(row.get('origin_lon', row.get('origin_longitude', 0.0))),
                destination_lat=float(row.get('destination_lat', row.get('destination_latitude', 0.0))),
                destination_lon=float(row.get('destination_lon', row.get('destination_longitude', 0.0))),
                priority=str(row.get('priority', 'MEDIUM')),
                customer_phone=str(row.get('customer_phone', '0000000000')),
                customer_email=c_email,
                status=str(row.get('status', 'PENDING')),
                risk_score=str(row.get('risk_score', 'LOW'))
            )
            shipments_to_load.append(s)
        except Exception as ex:
            pass
    crud.load_shipments_bulk(db, shipments_to_load)

dataset_folder = "datasets"
if not os.path.exists(dataset_folder):
    os.makedirs(dataset_folder)

csv_files = [f for f in os.listdir(dataset_folder) if f.endswith('.csv')]

st.markdown("<b>Dataset Selection</b>", unsafe_allow_html=True)
c_sel, c_upl = st.columns(2)
with c_sel:
    selected_dataset = st.selectbox("Select Dataset", ["-- Select --"] + csv_files)
with c_upl:
    uploaded_file = st.file_uploader("Or Upload New Dataset (CSV)", type=["csv"], label_visibility="collapsed")

if uploaded_file is not None:
    try:
        with open(os.path.join(dataset_folder, uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
        df_upload = pd.read_csv(os.path.join(dataset_folder, uploaded_file.name))
        load_data(df_upload)
        st.success("Uploaded successfully. Please select it from the dropdown to load.")
    except Exception as e:
        st.error(f"Upload error: {e}")

if selected_dataset == "-- Select --":
    st.info("Please select or upload a dataset to begin monitoring.")
    st.stop()

# AFTER dataset selection:
df_selected = pd.read_csv(os.path.join(dataset_folder, selected_dataset))

selected_ids = set(df_selected['shipment_id'].astype(str))
existing_ids = {str(s.shipment_id) for s in crud.get_shipments(db)}

if not selected_ids.issubset(existing_ids):
    load_data(df_selected)

db_shipments = [s for s in crud.get_shipments(db) if str(s.shipment_id) in selected_ids]
shipment_dicts = [
    {
        "ID": s.shipment_id, "Origin": s.origin, "Destination": s.destination,
        "Priority": s.priority, "Status": s.status, "Risk Level": str(s.risk_score).title()
    } for s in db_shipments
]
df_display = pd.DataFrame(shipment_dicts)

st.markdown("<hr/>", unsafe_allow_html=True)
st.markdown("<b>Shipment Table</b>", unsafe_allow_html=True)
st.dataframe(df_display, use_container_width=True, hide_index=True, height=200)

st.markdown("<hr/>", unsafe_allow_html=True)
st.markdown("<b>Global Risk Factor Analytics</b>", unsafe_allow_html=True)

total_count = len(df_display)
high_risk_count = len(df_display[df_display['Risk Level'] == 'High'])
medium_risk_count = len(df_display[df_display['Risk Level'] == 'Medium'])
low_risk_count = len(df_display[df_display['Risk Level'] == 'Low'])

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.markdown(f"<div class='panel' style='text-align:center;'><b>Total Shipments</b><br><h2 style='margin:0;'>{total_count}</h2></div>", unsafe_allow_html=True)
col_m2.markdown(f"<div class='panel' style='text-align:center; color:#ef4444;'><b>High Risk</b><br><h2 style='margin:0;'>{high_risk_count}</h2></div>", unsafe_allow_html=True)
col_m3.markdown(f"<div class='panel' style='text-align:center; color:#f59e0b;'><b>Medium Risk</b><br><h2 style='margin:0;'>{medium_risk_count}</h2></div>", unsafe_allow_html=True)
col_m4.markdown(f"<div class='panel' style='text-align:center; color:#10b981;'><b>Low Risk</b><br><h2 style='margin:0;'>{low_risk_count}</h2></div>", unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)
st.markdown("<b>Live Shipment Tracking & AI Analysis</b>", unsafe_allow_html=True)
c_analyze, _ = st.columns([1, 2])
with c_analyze:
    shipment_selection = st.selectbox("Analyze Shipment ID", ["-- Select --"] + df_display['ID'].tolist())

if shipment_selection != "-- Select --":
    selected_shipment = next(s for s in db_shipments if s.shipment_id == shipment_selection)
    
    if st.session_state.get('last_analyzed') != shipment_selection:
        st.session_state['alert_sent'] = set()
        st.session_state['email_sent'] = set()
        st.session_state['last_analyzed'] = shipment_selection

    with st.spinner("Analyzing realtime API signals & AI models..."):
        weather = weather_api.get_weather_disruption(selected_shipment.origin_lat, selected_shipment.origin_lon, selected_shipment.risk_score)
        traffic = traffic_api.get_traffic_disruption(selected_shipment.origin_lat, selected_shipment.origin_lon, selected_shipment.risk_score)
        news = news_api.get_news_disruption(selected_shipment.origin, selected_shipment.risk_score)
        
        base_risk = ai_analysis.calculate_risk_score(weather, traffic, news, selected_shipment.priority)
        s_dict = {"origin": selected_shipment.origin, "destination": selected_shipment.destination, "priority": selected_shipment.priority}
        
        # Merge if EMERGENCY
        if selected_shipment.status == "EMERGENCY":
            base_risk = "High"

        ai_res = ai_analysis.analyze_shipment_risk(s_dict, weather, traffic, news, base_risk)
        has_alt = ai_res.get("AlternateRoute") and ai_res.get("AlternateRoute") != "N/A"
        
        c_map, c_ai = st.columns([3, 2])
        with c_map:
            st.markdown("<b>Real-Time Tracking Map</b>", unsafe_allow_html=True)
            st.markdown("<div class='panel' style='padding:4px;'>", unsafe_allow_html=True)
            mid_lat = (selected_shipment.origin_lat + selected_shipment.destination_lat) / 2
            mid_lon = (selected_shipment.origin_lon + selected_shipment.destination_lon) / 2
            m = folium.Map(location=[mid_lat, mid_lon], zoom_start=6, tiles='CartoDB positron')
            
            folium.Marker([selected_shipment.origin_lat, selected_shipment.origin_lon], popup=f"Origin: {selected_shipment.origin}", icon=folium.Icon(color="green")).add_to(m)
            folium.Marker([selected_shipment.destination_lat, selected_shipment.destination_lon], popup=f"Destination: {selected_shipment.destination}", icon=folium.Icon(color="red")).add_to(m)
            
            r_color = "#ef4444" if base_risk == "High" else "#3b82f6"
            folium.PolyLine([[selected_shipment.origin_lat, selected_shipment.origin_lon], [selected_shipment.destination_lat, selected_shipment.destination_lon]], color=r_color, weight=4, opacity=0.8).add_to(m)
            
            # Truck location mock
            t_lat = selected_shipment.origin_lat + (selected_shipment.destination_lat - selected_shipment.origin_lat) * 0.4
            t_lon = selected_shipment.origin_lon + (selected_shipment.destination_lon - selected_shipment.origin_lon) * 0.4
            folium.Marker([t_lat, t_lon], tooltip="Truck Location", icon=folium.Icon(icon="truck", prefix="fa", color="blue")).add_to(m)
            
            if base_risk in ["High", "Medium"] and has_alt:
                alt_mid_lat = mid_lat + 0.8
                alt_mid_lon = mid_lon + 0.1
                folium.PolyLine(
                    [[selected_shipment.origin_lat, selected_shipment.origin_lon], [alt_mid_lat, alt_mid_lon], [selected_shipment.destination_lat, selected_shipment.destination_lon]],
                    color="#10b981", weight=4, opacity=0.9, dash_array='8', tooltip=f"Alternate: {ai_res.get('AlternateRoute')}"
                ).add_to(m)
            
            st_folium(m, use_container_width=True, height=350, returned_objects=[])
            st.markdown("</div>", unsafe_allow_html=True)

        with c_ai:
            st.markdown("<b>AI Analysis Panel</b>", unsafe_allow_html=True)
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown(f"<b>Risk Level:</b> <span style='color:{'#ef4444' if base_risk=='High' else '#f59e0b' if base_risk=='Medium' else '#10b981'};'>{base_risk}</span>", unsafe_allow_html=True)
            st.markdown(f"**Disruption Reason:** {ai_res.get('Explanation', 'None')}")
            st.markdown(f"**Predicted Delay:** {ai_res.get('PredictedDelay', 'On time')}")
            st.markdown(f"**Suggested Action:** {ai_res.get('RecommendedAction', 'Proceed')}")
            if has_alt:
                st.markdown(f"**Alternate Route:** <span style='color:#10b981;'>{ai_res.get('AlternateRoute')}</span>", unsafe_allow_html=True)
            
            st.markdown("<br/><b>Disruption Signals</b>", unsafe_allow_html=True)
            st.markdown(f"<small>☁ Weather: {weather['details']} ({weather['severity']}) <br/>🚗 Traffic: {traffic['details']} ({traffic['severity']}) <br/>📰 News: {news['details']} ({news['severity']})</small>", unsafe_allow_html=True)
            
            if base_risk == "High":
                st.markdown("<div class='alert-panel'>⚠ Route Rerouted Due to High Risk</div>", unsafe_allow_html=True)
                
                if shipment_selection not in st.session_state['alert_sent']:
                    # Play sound
                    if os.path.exists("alert.wav"):
                        with open("alert.wav", "rb") as f:
                            b64 = base64.b64encode(f.read()).decode()
                            st.markdown(f'<audio autoplay="true" style="display:none;"><source src="data:audio/wav;base64,{b64}" type="audio/wav"></audio>', unsafe_allow_html=True)
                    
                    # Send SMS
                    ph = selected_shipment.customer_phone
                    if ph and str(ph) != "0000000000":
                        notification_service.send_sms(ph, f"Delay expected for shipment {shipment_selection}. Route rerouted.")
                    
                    st.session_state['alert_sent'].add(shipment_selection)
                
                # Rerouting Email
                if shipment_selection not in st.session_state['email_sent']:
                    email = selected_shipment.customer_email
                    if email and "@" in email:
                        email_service.send_reroute_email(email, shipment_selection)
                    st.session_state['email_sent'].add(shipment_selection)
            st.markdown("</div>", unsafe_allow_html=True)



st.markdown("<hr/>", unsafe_allow_html=True)
st.markdown("<b>Risk Distribution Charts</b>", unsafe_allow_html=True)

col_donut, col_bar = st.columns(2)
with col_donut:
    st.markdown("<div class='panel' style='padding:5px;'>", unsafe_allow_html=True)
    if not df_display.empty:
        rcounts = df_display['Risk Level'].value_counts().reset_index()
        rcounts.columns = ['Risk Level', 'Total shipments']
        fig_pie = px.pie(rcounts, values='Total shipments', names='Risk Level', hole=0.5,
                         color='Risk Level', color_discrete_map={'Low':'green', 'Medium':'orange', 'High':'red'},
                         title="Total shipments by risk level")
        fig_pie.update_layout(
            margin=dict(t=30, b=10, l=10, r=10), 
            title_font_size=14,
            annotations=[dict(text=f'Total<br>{total_count}', x=0.5, y=0.5, font_size=18, showarrow=False)]
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_bar:
    st.markdown("<div class='panel' style='padding:5px;'>", unsafe_allow_html=True)
    if not df_display.empty:
        b_data = df_display.groupby(['Priority', 'Risk Level']).size().reset_index(name='Count')
        fig_bar = px.bar(b_data, x='Priority', y='Count', color='Risk Level', barmode='group',
                         color_discrete_map={'Low':'green', 'Medium':'orange', 'High':'red'},
                         title="Risk assessment by shipment priority",
                         category_orders={'Priority': ['LOW', 'MEDIUM', 'HIGH'], 'Risk Level': ['Low', 'Medium', 'High']})
        fig_bar.update_layout(margin=dict(t=30, b=10, l=10, r=10), title_font_size=14)
        st.plotly_chart(fig_bar, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)



db.close()
