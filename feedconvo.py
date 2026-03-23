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
bg_url = "https://images.unsplash.com/photo-1516467508483-a7212febe31a"

st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("{bg_url}");
        background-attachment: fixed;
        background-size: cover;
    }}
    .main {{ 
        background-color: rgba(255, 255, 255, 0.94); 
        padding: 30px; 
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }}
    .stMetric {{ background-color: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; }}
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
    menu = st.radio("GO TO:", ["📊 Dashboard", "🧪 Feed Solver", "📈 FCR Tracker", "📚 Ingredient Guide", "🛒 Marketplace"])

    # Global Logic
    active_birds = max(0, flock_size - mortality)
    age_days = (datetime.date.today() - start_date).days
    total_potential_yield = active_birds * harvest_target

# --- 5. PAGE LOGIC ---

if menu == "📊 Dashboard":
    st.title(f"📊 Dashboard: Day {age_days}")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Live Birds", f"{active_birds}")
    m2.metric("Current Age", f"{age_days} Days")
    m3.metric("Est. Harvest Yield", f"{total_potential_yield:.1f} kg")

    st.divider()
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

elif menu == "📈 FCR Tracker":
    st.title("📈 Feed Conversion Ratio (FCR) Tracker")
    st.info("FCR measures how efficiently your birds turn feed into meat. Lower is better!")
    
    col1, col2 = st.columns(2)
    total_feed_consumed = col1.number_input("Total Feed Consumed to Date (kg)", min_value=0.1, value=10.0)
    current_avg_weight = col2.number_input("Current Average Bird Weight (kg)", min_value=0.01, value=0.5)
    
    total_biomass = active_birds * current_avg_weight
    fcr = total_feed_consumed / total_biomass if total_biomass > 0 else 0
    
    st.divider()
    res1, res2 = st.columns(2)
    res1.metric("Current FCR", f"{fcr:.2f}")
    
    if fcr <= 1.6:
        res2.success("Excellent Efficiency! 🏆")
    elif fcr <= 1.9:
        res2.warning("Good, but check for feed waste. ⚠️")
    else:
        res2.error("High FCR! Check for disease or poor feed quality. 🚨")

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
