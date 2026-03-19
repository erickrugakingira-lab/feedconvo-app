import streamlit as st
import pulp
import pandas as pd
import datetime
import plotly.express as px
import base64

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="FeedConvo: Poultry Manager", layout="wide", page_icon="🐓")

# --- 2. BACKGROUND IMAGE LOGIC ---
IMG_FILENAME = "imgbin_5c1e0f1844143bbe86237e6decb92448.jpg"

def get_base64_image(file):
    try:
        with open(file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except: return None

img_data = get_base64_image(IMG_FILENAME)
bg_style = f"url('data:image/jpg;base64,{img_data}')" if img_data else "none"

# --- 3. THE "VISIBILITY & BRANDING" STYLE ---
st.markdown(f"""
<style>
    .stApp {{
        background: linear-gradient(rgba(255,255,255,0.82), rgba(255,255,255,0.82)), {bg_style};
        background-size: cover; background-attachment: fixed;
    }}
    section[data-testid="stSidebar"] {{ background-color: rgba(27, 67, 50, 0.95) !important; }}
    section[data-testid="stSidebar"] .stMarkdown h2, 
    section[data-testid="stSidebar"] label {{ color: white !important; }}
    
    /* Input Visibility Fix */
    input {{ color: black !important; background-color: white !important; }}
    div[data-baseweb="input"] {{ background-color: white !important; border-radius: 8px; }}

    /* UI Cards */
    div.stMetric, .stTable, .market-card {{
        background: rgba(255, 255, 255, 0.9) !important;
        border-radius: 12px; padding: 20px; border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }}
    .buy-btn {{
        display: inline-block; padding: 10px 20px; background-color: #f2a900;
        color: #1b4332 !important; text-decoration: none; border-radius: 8px; 
        font-weight: bold; text-align: center; width: 100%;
    }}
    h1, h2, h3 {{ color: #1b4332; }}
</style>
""", unsafe_allow_html=True)

# --- 4. DATA STANDARDS & DEALERS ---
STANDARDS = {
    "Starter (Wk 1)": {"prot": 22.5, "en": 3000, "daily_feed_g": 25},
    "Grower (Wk 2-3)": {"prot": 20.0, "en": 3100, "daily_feed_g": 75},
    "Finisher (Wk 4+)": {"prot": 18.5, "en": 3250, "daily_feed_g": 150}
}

ING_DATA = {
    "Maize": {"prot": 9.0, "en": 3350},
    "Soya Meal": {"prot": 44.0, "en": 2500},
    "Fish Meal": {"prot": 55.0, "en": 2800},
    "Sunflower Cake": {"prot": 24.0, "en": 2300}
}

DEALER_LINKS = {
    "Maize": "https://wa.me/255XXXXXXXXX?text=Order+Maize",
    "Soya Meal": "https://wa.me/255XXXXXXXXX?text=Order+Soya",
    "Fish Meal": "https://wa.me/255XXXXXXXXX?text=Order+FishMeal",
    "Concentrate": "https://wa.me/255XXXXXXXXX?text=Order+Concentrate"
}

# --- 5. SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("🚜 Farm Manager")
    flock_name = st.text_input("Flock ID", value="Batch-01")
    flock_size = st.number_input("Total Birds Started", min_value=1, value=100)
    start_date = st.date_input("Hatch Date", datetime.date.today() - datetime.timedelta(days=10))
    mortality = st.number_input("Mortality (Dead Birds)", min_value=0, value=0)
    st.divider()
    menu = st.radio("NAVIGATION", ["📊 Dashboard", "🧪 Feed Solver", "🛒 Marketplace"])

# CORE CALCULATIONS
active_birds = flock_size - mortality
age_days = (datetime.date.today() - start_date).days
current_stage = "Starter (Wk 1)" if age_days < 8 else ("Grower (Wk 2-3)" if age_days < 22 else "Finisher (Wk 4+)")

# --- 6. DASHBOARD TAB ---
if menu == "📊 Dashboard":
    st.title(f"Dashboard: {flock_name}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Flock", f"{active_birds} Birds")
    col2.metric("Age", f"{age_days} Days")
    col3.metric("Feed Stage", current_stage.split()[0])

    # NEW: FEED CALCULATOR SECTION
    st.subheader("📦 Inventory Planning")
    daily_req_kg = (active_birds * STANDARDS[current_stage]["daily_feed_g"]) / 1000
    weekly_req_kg = daily_req_kg * 7
    bags_needed = weekly_req_kg / 50  # Assuming 50kg bags
    
    st.info(f"💡 Based on your **{active_birds} birds**, you need approx **{bags_needed:.1f} bags (50kg)** of feed for the next 7 days.")

    st.subheader("📈 Performance Curve")
    chart_data = pd.DataFrame({
        "Age (Days)": [0, 7, 14, 21, 28, 35, 42],
        "Target Weight (kg)": [0.04, 0.18, 0.45, 0.90, 1.40, 1.90, 2.30]
    })
    fig = px.line(chart_data, x="Age (Days)", y="Target Weight (kg)", title="Breed Standard Growth")
    st.plotly_chart(fig, use_container_width=True)

# --- 7. FEED SOLVER TAB ---
elif menu == "🧪 Feed Solver":
    st.title("Least-Cost Feed Solver")
    st.write(f"Formulating for: **{current_stage}**")
    
    avail = st.multiselect("Available Ingredients:", list(ING_DATA.keys()), default=["Maize", "Soya Meal"])
    prices = {i: st.number_input(f"{i} (TSH/kg)", value=850 if i=="Maize" else 2600) for i in avail}
    
    if st.button("Calculate Best Formula"):
        prob = pulp.LpProblem("FeedMix", pulp.LpMinimize)
        vars = pulp.LpVariable.dicts("KG", avail, lowBound=0)
        
        prob += pulp.lpSum([vars[i] * prices[i] for i in avail]) # Cost
        prob += pulp.lpSum([vars[i] for i in avail]) == 100    # Total 100kg
        prob += pulp.lpSum([vars[i] * ING_DATA[i]["prot"] for i in avail]) >= STANDARDS[current_stage]["prot"] * 100
        
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        if pulp.LpStatus[prob.status] == 'Optimal':
            st.success(f"Optimized Cost: {int(sum(vars[i].varValue * prices[i] for i in avail)):,} TSH per 100kg")
            st.subheader("Mixing Guide & Quick Order")
            for i in avail:
                if vars[i].varValue > 0:
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"**{i}**: {vars[i].varValue:.2f} kg")
                    c2.markdown(f'<a href="{DEALER_LINKS.get(i, "#")}" target="_blank" class="buy-btn">🛒 Buy</a>', unsafe_allow_html=True)
        else:
            st.error("Cannot balance nutrients with these ingredients.")

# --- 8. MARKETPLACE TAB ---
elif menu == "🛒 Marketplace":
    st.title("Partner Marketplace")
    st.write("Verified dealers for high-quality ingredients.")
    
    m_cols = st.columns(3)
    for idx, (item, link) in enumerate(DEALER_LINKS.items()):
        with m_cols[idx % 3]:
            st.markdown(f"""
            <div class="market-card">
                <h3>{item}</h3>
                <p>Top Quality Standards</p>
                <a href="{link}" target="_blank" class="buy-btn">Contact Dealer</a>
            </div>
            """, unsafe_allow_html=True)
