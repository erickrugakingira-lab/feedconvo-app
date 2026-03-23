import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import os

# --- 1. GLOBAL CONFIGURATION ---
st.set_page_config(page_title="FeedConvo Poultry Pro", layout="wide", page_icon="🐔")

# --- 2. THE DATABASES (Global Scope) ---
ING_DATABASE = {
    "Maize": {
        "img": "maize_grain.jpg", 
        "prot": 9.0, "en": 3350, 
        "details": "Primary energy source. High risk of Aflatoxins in humid areas.",
        "qc": [
            "✅ Moisture: Must be below 13% (grains should 'snap' when bitten).",
            "✅ Color: Uniform yellow; no black or greenish-blue dust (mold).",
            "✅ Smell: No musty or fermented odor.",
            "✅ Purity: No weevils or stones."
        ],
        "price_per_kg": 800
    },
    "Soya Meal": {
        "img": "soyameal.jpg",
        "prot": 44.0, "en": 2500, 
        "details": "High-quality vegetable protein. Requires proper toasting.",
        "qc": [
            "✅ Color: Light tan/golden. White is undercooked; dark brown is burnt.",
            "✅ Texture: Fine flakes; no large hard clumps.",
            "✅ Smell: Fresh, nutty aroma. No raw bean smell."
        ],
        "price_per_kg": 2200
    },
    "Fish Meal": {
        "img": "fishmeal.jpg",
        "prot": 55.0, "en": 2800, 
        "details": "Animal protein with essential amino acids.",
        "qc": [
            "✅ Salt: Should not be extremely salty to the taste.",
            "✅ Texture: No heavy grit or sand when rubbed.",
            "✅ Smell: Strong fishy smell is okay; 'rotten' is a fail."
        ],
        "price_per_kg": 3500
    },
    "Sunflower Cake": {
        "img": "sunflower_cake.jpeg",
        "prot": 24.0, "en": 2300, 
        "details": "Fiber source. Good for cost reduction in older birds.",
        "qc": [
            "✅ Fiber: No excessive black hulls (causes diarrhea).",
            "✅ Oil: Should not feel greasy or smell rancid.",
            "✅ Hardness: Should break easily by hand."
        ],
        "price_per_kg": 1100
    }
}

STANDARDS = {
    "Starter (Wk 1-2)": 22.0, 
    "Grower (Wk 3-4)": 20.0, 
    "Finisher (Wk 5+)": 18.0
}

# --- 3. CUSTOM STYLING & BACKGROUND ---
# Use your RAW GitHub URL here
bg_url = "https://raw.githubusercontent.com/erickrugakingira-lab/feedconvo-app/main/broiler_chicken.png"

st.markdown(f"""
    <style>
    /* 1. The Background Photo */
    .stApp {{
        background-image: url("{bg_url}");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
    }}

    /* 2. The Main Content Box (The "Glass" Effect) */
    .main {{ 
        background-color: rgba(255, 255, 255, 0.85); /* Increase this to 0.98 for more opaque white */
        padding: 40px; 
        border-radius: 25px;
        margin-top: 15px;
        margin-bottom: 15px;
        box-shadow: 0 10px 15px rgba(0,0,0,0.2); /* Adds a shadow to lift the box off the background */
    }}

    /* 3. The Sidebar (Making it solid so it doesn't clash) */
    [data-testid="stSidebar"] {{
        background-color: #f8f9fa;
        border-right: 1px solid #eee;
    }}

    /* 4. Making Text Bold & Dark for readability */
    h1, h2, h3 {{
        color: #1b4332; /* Deep forest green */
        font-weight: 800;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR & GLOBAL CALCULATIONS ---
with st.sidebar:
    st.header("🚜 Farm Manager")
    flock_size = st.number_input("Birds Started", min_value=1, value=100)
    mortality = st.number_input("Mortality (Deaths)", min_value=0, value=0)
    harvest_target = st.number_input("Target Weight (kg)", min_value=0.1, value=2.5)
    start_date = st.date_input("Hatch Date", datetime.date.today() - datetime.timedelta(days=14))
    
    st.divider()
    menu = st.radio("GO TO:", ["📊 Dashboard", "🧪 Feed Solver", "📚 Ingredient Guide", "🛒 Marketplace"])

    # Global Logic
    active_birds = max(0, flock_size - mortality)
    age_days = (datetime.date.today() - start_date).days
    total_potential_yield = active_birds * harvest_target

# --- 5. PAGE LOGIC ---

if menu == "📊 Dashboard":
    st.title(f"📊 Farm Command Center: Day {age_days}")
    
    # --- SECTION 1: LIVE FLOCK METRICS ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Live Birds", f"{active_birds}", delta=f"-{mortality} deaths", delta_color="inverse")
    m2.metric("Current Age", f"{age_days} Days")
    m3.metric("Est. Harvest Yield", f"{total_potential_yield:.1f} kg")

    st.divider()

    # --- SECTION 2: THE FCR TRACKER (EFFICIENCY) ---
    st.subheader("📈 Efficiency: Feed Conversion Ratio (FCR)")
    col_fcr1, col_fcr2 = st.columns([2, 1])
    
    with col_fcr1:
        total_feed_consumed = st.number_input("Total Feed Consumed to Date (kg)", min_value=0.1, value=10.0, help="Total kg of feed poured into feeders since Day 1.")
        current_avg_weight = st.number_input("Current Avg. Weight per Bird (kg)", min_value=0.01, value=0.5, step=0.05)
        
        # Calculation
        total_biomass = active_birds * current_avg_weight
        fcr = total_feed_consumed / total_biomass if total_biomass > 0 else 0
        
    with col_fcr2:
        st.metric("Current FCR", f"{fcr:.2f}")
        if fcr <= 1.6:
            st.success("Excellent! High profit margin. ✅")
        elif fcr <= 1.9:
            st.warning("Average. Watch for feed waste. ⚠️")
        else:
            st.error("Poor FCR! Check feed quality/health. 🚨")

    st.divider()

    # --- SECTION 3: THE ROI CALCULATOR (MONEY) ---
    st.subheader("💵 Profit & ROI Projection")
    
    with st.expander("🛠️ Adjust Costs & Market Prices"):
        cx, cy = st.columns(2)
        doc_cost = cx.number_input("Cost per Chick (TSH)", value=1500)
        market_price_kg = cy.number_input("Market Price per KG (TSH)", value=8500)
        other_costs = st.number_input("Other Costs (Meds, Labor, Heat)", value=50000)
        
    # Calculate Feed Cost based on actual consumption from FCR input
    # We use your database prices to find the cost per kg of feed
    avg_feed_price = (ING_DATABASE["Maize"]["price_per_kg"] * 0.65) + \
                     (ING_DATABASE["Soya Meal"]["price_per_kg"] * 0.35)
    
    current_investment = (flock_size * doc_cost) + (total_feed_consumed * avg_feed_price) + other_costs
    expected_revenue = total_potential_yield * market_price_kg
    net_profit = expected_revenue - current_investment
    roi_percent = (net_profit / current_investment) * 100 if current_investment > 0 else 0

    r1, r2, r3 = st.columns(3)
    r1.metric("Total Investment", f"{int(current_investment):,} TSH")
    r2.metric("Expected Revenue", f"{int(expected_revenue):,} TSH")
    
    if net_profit > 0:
        r3.metric("Projected Profit", f"{int(net_profit):,} TSH", f"{roi_percent:.1f}% ROI")
    else:
        r3.metric("Projected Loss", f"{int(net_profit):,} TSH", f"{roi_percent:.1f}% ROI", delta_color="inverse")

    st.divider()

    # --- SECTION 4: VACCINATION ---
    st.subheader("💉 Vaccination Schedule")
    vac_df = pd.DataFrame({
        "Day": [1, 7, 14, 21, 28, 35],
        "Vaccine": ["Marek's/IB", "Gumboro 1", "Newcastle 1", "Gumboro 2", "Newcastle 2", "Fowl Pox"],
        "Status": ["✅ Done" if age_days >= d else "⏳ Pending" for d in [1, 7, 14, 21, 28, 35]]
    })
    st.table(vac_df)

elif menu == "🧪 Feed Solver":
    st.title("🧪 Precision Feed Solver")
    
    col_a, col_b = st.columns(2)
    with col_a:
        stage = st.selectbox("Select Growth Stage:", list(STANDARDS.keys()))
        target_prot = STANDARDS[stage]
    with col_b:
        total_to_produce = st.number_input("Total Feed to Produce (kg)", min_value=1.0, value=50.0)
    
    use_premix = st.checkbox("Include 5% Premix/Minerals (Recommended)", value=True)
    
    # Calculation
    m_prot, s_prot = ING_DATABASE["Maize"]["prot"], ING_DATABASE["Soya Meal"]["prot"]
    usable_target = target_prot / 0.95 if use_premix else target_prot
    premix_kg = total_to_produce * 0.05 if use_premix else 0
    remaining_kg = total_to_produce - premix_kg
    
    soya_ratio = (usable_target - m_prot) / (s_prot - m_prot)
    maize_kg, soya_kg = remaining_kg * (1 - soya_ratio), remaining_kg * soya_ratio

    st.subheader(f"📋 Recipe for {total_to_produce}kg")
    recipe_df = pd.DataFrame({
        "Ingredient": ["Maize Grain", "Soya Meal", "Premix"],
        "Weight (kg)": [f"{maize_kg:.2f} kg", f"{soya_kg:.2f} kg", f"{premix_kg:.2f} kg"]
    })
    st.table(recipe_df)

    with st.expander("🥣 Detailed Mixing Instructions"):
        st.write("""
        1. **Layering:** Spread Maize first, then Soya on top.
        2. **Pre-Mix:** Mix your Premix in a small bucket with 2kg of Maize before adding to the big pile.
        3. **The 3-Shovel Rule:** Turn the pile at least 3 times until the color is uniform.
        """)

elif menu == "📚 Ingredient Guide":
    st.title("📚 Quality Control Guide")
    for name, info in ING_DATABASE.items():
        with st.expander(f"🔍 Inspecting {name}"):
            c1, c2 = st.columns([1, 2])
            with c1:
                if os.path.exists(info["img"]): st.image(info["img"])
                else: st.warning("Photo missing on GitHub")
            with c2:
                for check in info["qc"]: st.write(check)

elif menu == "🛒 Marketplace":
    st.title("🛒 Supplier Marketplace")
    cols = st.columns(2)
    for i, (name, info) in enumerate(ING_DATABASE.items()):
        with cols[i % 2]:
            st.markdown(f"""
            <div style="border:1px solid #ddd; padding:15px; border-radius:10px; margin-bottom:10px; background:white;">
                <h4>{name}</h4>
                <p>Price: <b>{info['price_per_kg']} TSH/kg</b></p>
                <a href="https://wa.me/255700000000" target="_blank"><button style="width:100%; background:#1b4332; color:white; border:none; padding:8px; border-radius:5px; cursor:pointer;">Order Now</button></a>
            </div>
            """, unsafe_allow_html=True)
