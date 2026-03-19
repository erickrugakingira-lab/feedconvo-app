import streamlit as st
import pulp
import pandas as pd
import datetime
import plotly.express as px
import base64
import urllib.parse
import os

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="FeedConvo: QC & Solver", layout="wide", page_icon="🛡️")

# --- 2. IMAGE LOADER ---
def get_base64_image(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

bg_data = get_base64_image("broiler chicken.png")
bg_style = f"url('data:image/png;base64,{bg_data}')" if bg_data else "none"

# --- 3. STYLING (Visibility & QC Cards) ---
st.markdown(f"""
<style>
    .stApp {{
        background: linear-gradient(rgba(255,255,255,0.92), rgba(255,255,255,0.92)), {bg_style};
        background-size: cover; background-attachment: fixed;
    }}
    
    /* Sidebar Text Visibility */
    section[data-testid="stSidebar"] {{ background-color: rgba(27, 67, 50, 0.95) !important; }}
    section[data-testid="stSidebar"] .stMarkdown h2, 
    section[data-testid="stSidebar"] label {{ color: white !important; font-weight: bold; }}

    /* CRITICAL: Fix for Invisible Input Text */
    input {{ 
        color: #000000 !important; 
        background-color: #FFFFFF !important; 
    }}
    
    /* Ensuring the box itself is visible with a border */
    div[data-baseweb="input"] {{ 
        background-color: #FFFFFF !important; 
        border: 2px solid #1b4332 !important; 
        border-radius: 8px; 
    }}
</style>
""", unsafe_allow_html=True)

# --- 4. DATA & QC CHECKLISTS ---
ING_DATABASE = {
    "Maize": {
        "file": "maize grain.jpg", "prot": 9.0, "en": 3350,
        "details": "Energy source. High risk of Aflatoxins.",
        "qc": ["Moisture < 13% (Grain cracks when bitten)", "No visible green/black mold", "No musty or fermented smell", "No insect/weevil damage"],
        "link": "https://wa.me/255XXXXXXXXX"
    },
    "Soya Meal": {
        "file": "soyameal.jpg", "prot": 44.0, "en": 2500,
        "details": "Main protein. Check toasting quality.",
        "qc": ["Color is light tan/gold (not white/raw)", "Nutty aroma (not beany/raw)", "Texture is flaky, not clumped/damp"],
        "link": "https://wa.me/255XXXXXXXXX"
    },
    "Fish Meal": {
        "file": "fishmeal.jpg", "prot": 55.0, "en": 2800,
        "details": "Animal protein. Check salt and freshness.",
        "qc": ["Low salt content (not crusty)", "No 'rotten' or overly 'oily' smell", "Free from sand/grit contamination"],
        "link": "https://wa.me/255XXXXXXXXX"
    },
    "Sunflower Cake": {
        "file": "sunflower.jpg", "prot": 24.0, "en": 2300,
        "details": "Fiber source. Watch for excessive hulls.",
        "qc": ["Minimal black hulls (too much fiber is bad)", "No dampness or caking", "Consistent brown color"],
        "link": "https://wa.me/255XXXXXXXXX"
    }
}

STANDARDS = {"Starter (Wk 1)": 22.5, "Grower (Wk 2-3)": 20.0, "Finisher (Wk 4+)": 18.5}

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("🚜 Farm Manager")
    menu = st.radio("GO TO:", ["📊 Dashboard", "🧪 Feed Solver", "📚 Ingredient Guide", "🛒 Marketplace"])
    st.divider()
    flock_size = st.number_input("Birds", value=100)
    start_date = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=7))

# Calculations
age_days = (datetime.date.today() - start_date).days
current_stage = "Starter (Wk 1)" if age_days < 8 else ("Grower (Wk 2-3)" if age_days < 22 else "Finisher (Wk 4+)")

# --- 6. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title(f"📈 Performance Tracking: {age_days} Days")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Live Flock Size", f"{flock_size} Birds")
    with col2:
        st.metric("Current Phase", current_stage)

    st.subheader("Weight Growth Curve (Standard vs. Target)")
    
    # Growth data based on Tanzanian Broiler Standards
    growth_data = pd.DataFrame({
        "Day": [0, 7, 14, 21, 28, 35, 42],
        "Target Weight (g)": [42, 185, 450, 910, 1450, 1980, 2400]
    })
    
    # Create the visual graph
    fig = px.line(growth_data, x="Day", y="Target Weight (g)", 
                 title="Standard Broiler Growth Curve",
                 markers=True, line_shape="spline")
    fig.update_traces(line_color='#1b4332')
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.info(f"💡 At Day {age_days}, your birds should be approaching {growth_data.iloc[min(age_days//7, 6)]['Target Weight (g)']} grams.")
    
# --- 8. FEED SOLVER ---
elif menu == "🧪 Feed Solver":
    st.title("Least-Cost Solver")
    avail = st.multiselect("Active Ingredients:", list(ING_DATABASE.keys()), default=["Maize", "Soya Meal"])
    prices = {i: st.number_input(f"{i} (TSH/kg)", value=850 if i=="Maize" else 2600) for i in avail}
    
    if st.button("Solve Formula"):
        prob = pulp.LpProblem("Feed", pulp.LpMinimize)
        vars = pulp.LpVariable.dicts("KG", avail, lowBound=0)
        prob += pulp.lpSum([vars[i] * prices[i] for i in avail])
        prob += pulp.lpSum([vars[i] for i in avail]) == 100
        prob += pulp.lpSum([vars[i] * ING_DATABASE[i]["prot"] for i in avail]) >= STANDARDS[current_stage] * 100
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        if pulp.LpStatus[prob.status] == 'Optimal':
            recipe = f"FeedConvo Recipe ({current_stage}):\n"
            for i in avail:
                if vars[i].varValue > 0:
                    st.success(f"**{i}**: {vars[i].varValue:.2f} kg")
                    recipe += f"- {i}: {vars[i].varValue:.2f} kg\n"
            st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(recipe)}" class="share-btn">📲 Share Recipe on WhatsApp</a>', unsafe_allow_html=True)

# --- 9. MARKETPLACE ---
elif menu == "🛒 Marketplace":
    st.title("Verified Suppliers")
    cols = st.columns(3)
    for idx, (name, meta) in enumerate(ING_DATABASE.items()):
        with cols[idx % 3]:
            img_b64 = get_base64_image(meta['file'])
            img_tag = f'<img src="data:image/jpg;base64,{img_b64}" style="width:100%; height:120px; object-fit:cover; border-radius:8px;">' if img_b64 else ""
            st.markdown(f'<div class="market-card">{img_tag}<h3>{name}</h3><a href="{meta["link"]}" class="buy-btn">Order</a></div>', unsafe_allow_html=True)
