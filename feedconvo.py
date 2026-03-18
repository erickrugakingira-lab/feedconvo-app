import streamlit as st
import pulp
import pandas as pd
import datetime
import plotly.express as px
import base64
import os

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="FeedConvo Pro", layout="wide", page_icon="🐓")

# --- 2. DEALER LINKS (Update these with real WhatsApp or Web links) ---
DEALER_LINKS = {
    "Maize": "https://wa.me/255XXXXXXXXX?text=I+need+Maize",
    "Soya Meal": "https://wa.me/255XXXXXXXXX?text=I+need+Soya",
    "Fish Meal": "https://wa.me/255XXXXXXXXX?text=I+need+FishMeal",
    "Vegetable Oil": "https://wa.me/255XXXXXXXXX",
    "Sunflower Cake": "https://wa.me/255XXXXXXXXX",
    "Concentrate": "https://wa.me/255XXXXXXXXX?text=Order+Concentrate"
}

# --- 3. BACKGROUND IMAGE HANDLER ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except: return ""

# Make sure this matches your uploaded image name exactly
img_name = "imgbin_5c1e0f1844143bbe86237e6decb92448.jpg"
img_64 = get_base64_of_bin_file(img_name)
bg_style = f"url('data:image/jpg;base64,{img_64}')" if img_64 else "none"

# --- 4. BRANDED STYLING ---
st.markdown(f"""
<style>
    .stApp {{
        background: linear-gradient(rgba(255,255,255,0.7), rgba(255,255,255,0.7)), {bg_style};
        background-size: cover; background-attachment: fixed;
    }}
    section[data-testid="stSidebar"] {{ background-color: rgba(27, 67, 50, 0.95) !important; }}
    section[data-testid="stSidebar"] * {{ color: white !important; }}
    div.stMetric, .stTable, .stDataFrame, .budget-box, .market-card {{
        background: rgba(255, 255, 255, 0.9) !important;
        border-radius: 12px !important; padding: 20px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        margin-bottom: 20px !important;
    }}
    .buy-btn {{
        display: inline-block; padding: 8px 15px; background-color: #f2a900;
        color: #1b4332 !important; text-decoration: none; border-radius: 5px;
        font-weight: bold; font-size: 0.8em; margin-top: 5px;
    }}
    h1, h2, h3 {{ color: #1b4332; font-weight: 800; }}
</style>
""", unsafe_allow_html=True)

# --- 5. DATA STANDARDS ---
STANDARDS = {
    "Starter (Week 1)": {"prot": 22.5, "energy": 3000, "total_stage_kg": 0.5},
    "Grower (Weeks 2-3)": {"prot": 20.0, "energy": 3100, "total_stage_kg": 1.5},
    "Finisher (Week 4+)": {"prot": 18.5, "energy": 3250, "total_stage_kg": 2.2}
}

ING_DATA = {
    "Maize": {"prot": 9.0, "en": 3350}, "Soya Meal": {"prot": 44.0, "en": 2500},
    "Fish Meal": {"prot": 55.0, "en": 2800}, "Vegetable Oil": {"prot": 0.0, "en": 8800},
    "Sunflower Cake": {"prot": 24.0, "en": 2300}
}

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("## 🚜 FeedConvo Pro")
    farmer_id = st.text_input("Farmer ID", value="Admin")
    num_birds = st.number_input("🐣 Flock Size", min_value=1, value=100)
    start_date = st.date_input("📅 Start Date", datetime.date.today() - datetime.timedelta(days=7))
    tab = st.radio("MENU", ["📊 Dashboard", "🧪 Feed Solver", "🛒 Marketplace"])

# --- 7. TABS LOGIC ---
if tab == "📊 Dashboard":
    st.title(f"Dashboard - {farmer_id}")
    age = (datetime.date.today() - start_date).days
    c1, c2, c3 = st.columns(3)
    c1.metric("Age", f"{age} Days")
    c2.metric("Water", f"{num_birds * 0.2:.1f} L/Day")
    c3.metric("Stage", "Starter" if age < 8 else ("Grower" if age < 22 else "Finisher"))
    st.info("Check the Marketplace for vaccine orders.")

elif tab == "🧪 Feed Solver":
    st.title("Feed Formulation")
    stage = st.selectbox("Formulate for:", list(STANDARDS.keys()))
    avail = st.multiselect("Ingredients:", list(ING_DATA.keys()), default=["Maize", "Soya Meal"])
    prices = {i: st.number_input(f"{i} Price/kg", value=780 if i=="Maize" else 2500) for i in avail}
    
    if st.button("Solve Mix"):
        prob = pulp.LpProblem("Feed", pulp.LpMinimize)
        vars = pulp.LpVariable.dicts("KG", avail, lowBound=0)
        prob += pulp.lpSum([vars[i] * prices[i] for i in avail])
        prob += pulp.lpSum([vars[i] for i in avail]) == 100
        prob += pulp.lpSum([vars[i] * ING_DATA[i]["prot"] for i in avail]) >= STANDARDS[stage]["prot"] * 100
        prob += pulp.lpSum([vars[i] * ING_DATA[i]["en"] for i in avail]) >= STANDARDS[stage]["energy"] * 100
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        if pulp.LpStatus[prob.status] == 'Optimal':
            st.subheader("Recipe & Order Links")
            for i in avail:
                if vars[i].varValue > 0:
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"**{i}**: {vars[i].varValue:.2f} kg")
                    c2.markdown(f'<a href="{DEALER_LINKS.get(i, "#")}" target="_blank" class="buy-btn">🛒 Buy</a>', unsafe_allow_html=True)
        else:
            st.error("Balance not possible.")

elif tab == "🛒 Marketplace":
    st.title("Marketplace")
    m_cols = st.columns(3)
    for idx, (item, link) in enumerate(DEALER_LINKS.items()):
        with m_cols[idx % 3]:
            st.markdown(f'<div class="market-card"><h3>{item}</h3><a href="{link}" target="_blank" class="buy-btn" style="display:block; text-align:center;">Order Now</a></div>', unsafe_allow_html=True)
