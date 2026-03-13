import streamlit as st

st.set_page_config(page_title="Select Role", layout="centered", page_icon="🚚")

st.markdown("""
<style>
    .stApp { background-color: #ffffff; color: #111827; }
    .header-box { text-align: center; color: #1f2937; margin-bottom: 2rem; font-size: 2.5rem; font-weight: bold; }
    .sub-box { text-align: center; color: #6b7280; margin-bottom: 30px; font-size: 1.2rem; }
    .stButton>button { padding: 20px; font-size: 1.2rem; font-weight: bold; border-radius: 10px; width: 100%; border: 1px solid #7dd3fc; background-color: #e0f2fe; color: #0c4a6e; cursor: pointer; transition: 0.2s; }
    .stButton>button:hover { background-color: #bae6fd; border-color: #38bdf8; transform: translateY(-2px); }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='header-box'>AI Logistics Risk Monitoring</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-box'>Select Your Role to Continue</div>", unsafe_allow_html=True)

st.write("")
st.write("")

c1, c2, c3 = st.columns(3)

with c1:
    if st.button("COMPANY DASHBOARD"):
        st.switch_page("pages/1_company_dashboard.py")
        
with c2:
    if st.button("DRIVER DASHBOARD"):
        st.switch_page("pages/2_driver_dashboard.py")
        
with c3:
    if st.button("CUSTOMER DASHBOARD"):
        st.switch_page("pages/3_customer_dashboard.py")
