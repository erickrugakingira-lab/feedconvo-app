import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

# --- 1. GLOBAL CONFIGURATION ---
st.set_page_config(page_title="FeedConvo Poultry Pro", layout="wide", page_icon="🐔")

# --- 2. THE DATABASES (Global Scope) ---
ING_DATABASE = {
    "Maize": {
        "img": "maize grain.jpg",
        "prot": 9.0, "en": 3350, 
        "details": "Primary energy source. High risk of Aflatoxins in humid areas.",
        "qc": ["Moisture < 13%", "No visible mold", "No musty smell"],
        "price_per_kg": 800
    },
    "Soya Meal": {
        "img": "soyameal.jpg"
        "prot": 44.0, "en": 2500, 
        "details": "High-quality vegetable protein. Check toasting to remove anti-nutrients.",
        "qc": ["Color is light tan", "Nutty aroma", "No clumping"],
        "price_per_kg": 2200
    },
    "Fish Meal": {
        "img": "fishmeal.jpg"
        "prot": 55.0, "en": 2800, 
        "details": "Animal protein with essential amino acids. Watch salt levels.",
        "qc": ["Low salt content", "No fishy/rotten smell"],
        "price_per_kg": 3500
    },
    "Sunflower Cake": {
        "prot": 24.0, "en": 2300, 
        "details": "Fiber source. Good for layers and finishers to reduce cost.",
        "qc": ["Minimal hulls", "No dampness"],
        "price_per_kg": 1100
    }
}

STANDARDS = {
    "Starter (Wk 1-2)": 22.0, 
    "Grower (Wk 3-4)": 20.0, 
    "Finisher (Wk 5+)": 18.0
}

# --- 3. CUSTOM STYLING (Including Background Image) ---
# Note: 'background.jpg' must be in your GitHub repo for this to work
st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("broiler chicken.png");
        background-attachment: fixed;
        background-size: cover;
    }}
    .main {{ 
        background-color: rgba(255, 255, 255, 0.85); 
        padding: 20px; 
        border-radius: 15px;
    }}
    .stMetric {{ background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }}
    </style>
    """, unsafe_allow_html=True)
# --- 4. SIDEBAR & GLOBAL LOGIC ---
with st.sidebar:
    st.header("🚜 Farm Manager")
    
    # Inputs
    flock_size = st.number_input("Total Birds Started", min_value=1, value=100)
    mortality = st.number_input("Mortality (Dead Birds)", min_value=0, value=0)
    harvest_target = st.number_input("Target Weight at Harvest (kg)", min_value=0.1, value=2.5, step=0.1)
    start_date = st.date_input("Hatch Date", datetime.date.today() - datetime.timedelta(days=7))
    
    st.divider()
    menu = st.radio("GO TO:", ["📊 Dashboard", "🧪 Feed Solver", "📚 Ingredient Guide", "🛒 Marketplace"])
    
    # Core Calculations (Performed here so all menu items can see them)
    active_birds = max(0, flock_size - mortality)
    age_days = (datetime.date.today() - start_date).days
    
    # Growth Curve Reference
    weights_g = [42, 185, 450, 910, 1450, 1980, 2400]
    idx = min(max(age_days // 7, 0), 6)
    current_std_weight_kg = weights_g[idx] / 1000
    
    total_harvest_yield_kg = active_birds * harvest_target

# --- 5. MAIN NAVIGATION LOGIC ---

# PAGE 1: DASHBOARD
if menu == "📊 Dashboard":
    st.title(f"📊 Performance & ROI: Day {age_days}")
    
    # Row 1: Key Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Live Birds", f"{active_birds}")
    m2.metric("Current Meat (est.)", f"{(active_birds * current_std_weight_kg):.1f} kg")
    m3.metric("Projected Harvest", f"{total_harvest_yield_kg:.1f} kg")

    st.divider()

    # Row 2: ROI Calculator
    st.subheader("💰 Profit & Loss Projection (At Harvest)")
    with st.expander("📝 Customize Costs & Market Prices"):
        col_a, col_b = st.columns(2)
        chick_cost = col_a.number_input("Cost per Chick (TSH)", value=1800)
        sale_price_kg = col_b.number_input("Selling Price per KG (TSH)", value=8500)
        other_costs_per_bird = st.number_input("Medication/Heat/Other per bird (TSH)", value=600)

    # Financial Math
    total_investment = (flock_size * chick_cost) + (active_birds * other_costs_per_bird)
    potential_revenue = total_harvest_yield_kg * sale_price_kg
    net_profit = potential_revenue - total_investment
    roi_pct = (net_profit / total_investment * 100) if total_investment > 0 else 0

    r1, r2, r3 = st.columns(3)
    r1.metric("Total Investment", f"{int(total_investment):,} TSH")
    r2.metric("Est. Revenue", f"{int(potential_revenue):,} TSH")
    if net_profit > 0:
        r3.metric("Projected Profit", f"{int(net_profit):,} TSH", f"{roi_pct:.1f}% ROI")
    else:
        r3.metric("Projected Loss", f"{int(net_profit):,} TSH", f"{roi_pct:.1f}% ROI", delta_color="inverse")

    st.divider()

    # Row 3: Vaccination Schedule
    st.subheader("💉 Vaccination & Health")
    vac_data = {
        "Day": [1, 7, 14, 21, 28],
        "Vaccine": ["Marek's / IB", "Gumboro (1st)", "Newcastle", "Gumboro (2nd)", "Newcastle Booster"],
        "Status": ["✅ Done" if age_days >= d else "⏳ Pending" for d in [1, 7, 14, 21, 28]]
    }
    st.table(pd.DataFrame(vac_data))

    # Row 4: Growth Chart
    st.subheader("📈 Growth Projection")
    df_growth = pd.DataFrame({"Day": [0, 7, 14, 21, 28, 35, 42], "Target (g)": weights_g})
    fig = px.line(df_growth, x="Day", y="Target (g)", markers=True)
    fig.update_traces(line_color='#1b4332', line_width=3)
    st.plotly_chart(fig, use_container_width=True)

# PAGE 2: FEED SOLVER
elif menu == "🧪 Feed Solver":
    st.title("🧪 Precision Feed Solver")
    stage = st.selectbox("Select Growth Stage:", list(STANDARDS.keys()))
    target_prot = STANDARDS[stage]
    
    st.info(f"Target Protein for {stage}: **{target_prot}%**")
    
    # Simple Pearson Square logic for Maize & Soya
    maize_p = ING_DATABASE["Maize"]["prot"]
    soya_p = ING_DATABASE["Soya Meal"]["prot"]
    
    soya_parts = abs(target_prot - maize_p)
    maize_parts = abs(soya_p - target_prot)
    total_parts = soya_parts + maize_parts
    
    soya_pct = (soya_parts / total_parts) * 100
    maize_pct = (maize_parts / total_parts) * 100
    
    st.success(f"**Recommended Mix:** {maize_pct:.1f}% Maize and {soya_pct:.1f}% Soya Meal")
    st.warning("Note: This is a basic 2-ingredient mix. Consider adding 5% premix/minerals.")

# PAGE 3: INGREDIENT GUIDE
elif menu == "📚 Ingredient Guide":
    st.title("📚 Quality Control Guide")
    for name, info in ING_DATABASE.items():
        with st.expander(f"🔍 {name}"):
            st.write(info["details"])
            st.write("**QC Checklist:**")
            for check in info["qc"]:
                st.write(f"- {check}")

# PAGE 4: MARKETPLACE
elif menu == "🛒 Marketplace":
    st.title("🛒 Supplier Marketplace")
    cols = st.columns(2)
    for i, (name, info) in enumerate(ING_DATABASE.items()):
        with cols[i % 2]:
            st.markdown(f"""
            <div style="border:1px solid #ddd; padding:15px; border-radius:10px; margin-bottom:10px;">
                <h4>{name}</h4>
                <p>Est. Price: <b>{info['price_per_kg']} TSH/kg</b></p>
                <button style="width:100%; border:none; background:#1b4332; color:white; padding:10px; border-radius:5px;">Contact Supplier</button>
            </div>
            """, unsafe_allow_html=True)
