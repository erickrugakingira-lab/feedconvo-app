import streamlit as st
import pulp
import pandas as pd
import datetime
import plotly.express as px
import base64
import os

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="FeedConvo: Full Manager", layout="wide", page_icon="🐓")

# --- 2. THE BACKGROUND FIX ---
# IMPORTANT: Ensure this filename matches your GitHub upload EXACTLY (case-sensitive)
IMG_FILENAME = "broiler chicken.png"

def get_base64_image(file):
    try:
        with open(file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except: return None

img_data = get_base64_image(IMG_FILENAME)
bg_style = f"url('data:image/jpg;base64,{img_data}')" if img_data else "none"

st.markdown(f"""
<style>
    .stApp {{
        background: linear-gradient(rgba(255,255,255,0.75), rgba(255,255,255,0.75)), {bg_style};
        background-size: cover; background-attachment: fixed;
    }}
    section[data-testid="stSidebar"] {{ background-color: rgba(27, 67, 50, 0.95) !important; }}
    section[data-testid="stSidebar"] * {{ color: white !important; }}
    div.stMetric, .stTable, .budget-box, .market-card {{
        background: rgba(255, 255, 255, 0.9) !important;
        border-radius: 12px; padding: 20px; border: 1px solid #ddd; margin-bottom: 15px;
    }}
    .buy-btn {{
        display: inline-block; padding: 6px 12px; background-color: #f2a900;
        color: #1b4332 !important; text-decoration: none; border-radius: 5px; font-weight: bold;
    }}
</style>
""", unsafe_allow_html=True)

# --- 3. DATA & DEALERS ---
STANDARDS = {
    "Starter (Wk 1)": {"prot": 22.5, "en": 3000, "std_wt": 0.20},
    "Grower (Wk 2-3)": {"prot": 20.0, "en": 3100, "std_wt": 0.75},
    "Finisher (Wk 4+)": {"prot": 18.5, "en": 3250, "std_wt": 2.20}
}

DEALER_LINKS = {
    "Maize": "https://wa.me/255XXXXXXXXX",
    "Soya Meal": "https://wa.me/255XXXXXXXXX",
    "Fish Meal": "https://wa.me/255XXXXXXXXX",
    "Concentrate": "https://wa.me/255XXXXXXXXX"
}

# --- 4. SIDEBAR MANAGEMENT ---
with st.sidebar:
    st.header("🚜 Flock Management")
    flock_size = st.number_input("Flock Size (Birds)", value=100)
    start_date = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=14))
    mortality = st.number_input("Dead Birds", min_value=0, value=2)
    st.divider()
    menu = st.radio("GO TO:", ["📊 Performance Dashboard", "🧪 Feed Solver", "🛒 Marketplace"])

# CALCULATIONS
active_birds = flock_size - mortality
age_days = (datetime.date.today() - start_date).days
current_stage = "Starter (Wk 1)" if age_days < 8 else ("Grower (Wk 2-3)" if age_days < 22 else "Finisher (Wk 4+)")

# --- 5. DASHBOARD (RESTORED) ---
if menu == "📊 Performance Dashboard":
    st.title("Flock Tracking System")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Active Flock", f"{active_birds} Birds")
    m2.metric("Age", f"{age_days} Days")
    m3.metric("Current Phase", current_stage.split()[0])

    st.subheader("📈 Growth Tracking")
    # Simulation of user weight tracking
    w1 = st.sidebar.number_input("Wk 1 Weight (kg)", value=0.18)
    w2 = st.sidebar.number_input("Wk 2 Weight (kg)", value=0.65)
    
    chart_data = pd.DataFrame({
        "Week": ["Wk 1", "Wk 2", "Wk 3", "Wk 4"],
        "Actual Weight": [w1, w2, None, None],
        "Standard Target": [0.20, 0.75, 1.45, 2.20]
    })
    fig = px.line(chart_data, x="Week", y=["Actual Weight", "Standard Target"], markers=True)
    st.plotly_chart(fig, use_container_width=True)

# --- 6. FEED SOLVER (RESTORED) ---
elif menu == "🧪 Feed Solver":
    st.title("Least-Cost Feed Solver")
    avail = st.multiselect("Active Ingredients:", ["Maize", "Soya Meal", "Fish Meal"], default=["Maize", "Soya Meal"])
    prices = {i: st.number_input(f"{i} Price/kg", value=800 if i=="Maize" else 2500) for i in avail}
    
    if st.button("Calculate Optimal Formula"):
        prob = pulp.LpProblem("Feed", pulp.LpMinimize)
        vars = pulp.LpVariable.dicts("KG", avail, lowBound=0)
        prob += pulp.lpSum([vars[i] * prices[i] for i in avail])
        prob += pulp.lpSum([vars[i] for i in avail]) == 100
        # Simple protein constraint for demo
        prob += pulp.lpSum([vars[i] * (9 if i=="Maize" else 44) for i in avail]) >= STANDARDS[current_stage]["prot"] * 100
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        if pulp.LpStatus[prob.status] == 'Optimal':
            st.success("Cheapest Mix Found!")
            for i in avail:
                if vars[i].varValue > 0:
                    c1, c2 = st.columns([3,1])
                    c1.write(f"**{i}**: {vars[i].varValue:.2f} kg")
                    c2.markdown(f'<a href="{DEALER_LINKS.get(i, "#")}" class="buy-btn">🛒 Buy</a>', unsafe_allow_html=True)
        else: st.error("Nutrients cannot be balanced.")

# --- 7. MARKETPLACE ---
elif menu == "🛒 Marketplace":
    st.title("Dealer Marketplace")
    cols = st.columns(3)
    for idx, (item, link) in enumerate(DEALER_LINKS.items()):
        with cols[idx % 3]:
            st.markdown(f'<div class="market-card"><h3>{item}</h3><a href="{link}" class="buy-btn" style="display:block; text-align:center;">Order from Dealer</a></div>', unsafe_allow_html=True)
