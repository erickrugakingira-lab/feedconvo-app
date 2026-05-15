import streamlit as st
import pandas as pd
import datetime
import os
from supabase import create_client, Client

# --- 1. GLOBAL CONFIGURATION ---
st.set_page_config(
    page_title="FeedConvo Pro", 
    layout="wide", 
    initial_sidebar_state="expanded", 
    page_icon="https://raw.githubusercontent.com/erickrugakingira-lab/feedconvo-app/main/assets/Main_logo.png"
)

# --- 2. SUPABASE CONNECTION ---
@st.cache_resource
def get_supabase() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"].strip()
        key = st.secrets["SUPABASE_KEY"].strip()
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        return None

supabase = get_supabase()

def save_to_supabase(flock_type, flock_id, age, birds, kpi_val, profit_val):
    if supabase:
        data = {
            "flock_type": flock_type,
            "flock_id": flock_id,
            "age_days": int(age),
            "active_birds": int(birds),
            "kpi_value": float(kpi_val),
            "profit_tsh": float(profit_val),
            "created_at": datetime.datetime.now().isoformat()
        }
        try:
            supabase.table("farm_records").insert(data).execute()
            st.success(f"✅ Data Synced to Supabase for {flock_id}!")
        except Exception as e:
            st.error(f"❌ Supabase Insert Failed: {e}")

# --- 3. THE DATABASES ---
# Added Maize Bran and refined nutrients
ING_DATABASE = {
    "Maize": {"img": "maize_grain.jpg", "prot": 9.0, "en": 3350, "price": 850},
    "Maize Bran": {"img": "maize_bran.jpg", "prot": 10.0, "en": 2200, "price": 450},
    "Soya Meal": {"img": "soyameal.jpg", "prot": 44.0, "en": 2500, "price": 2300},
    "BSF Larvae": {"img": "BSF_larvae.jpg", "prot": 50.0, "en": 3100, "price": 1500},
    "Vegetable Oil": {"img": "vegetable-oil.webp", "prot": 0.0, "en": 8800, "price": 3500},
    "Sunflower Cake": {"img": "sunflower_cake.jpeg", "prot": 28.0, "en": 2100, "price": 950}
}

STANDARDS = {
    "Broiler": {
        "Starter (Wk 1-2)": {"prot": 22.0, "en": 3000, "bsf_max": 0.05, "bran_max": 0.05},
        "Grower (Wk 3-4)": {"prot": 20.0, "en": 3100, "bsf_max": 0.10, "bran_max": 0.10},
        "Finisher (Wk 5+)": {"prot": 18.0, "en": 3200, "bsf_max": 0.15, "bran_max": 0.15}
    },
    "Layer": {
        "Chick Starter": {"prot": 18.0, "en": 2850, "bsf_max": 0.05, "bran_max": 0.05},
        "Pullet Grower": {"prot": 15.0, "en": 2750, "bsf_max": 0.10, "bran_max": 0.20},
        "Layer Phase 1": {"prot": 18.0, "en": 2800, "bsf_max": 0.12, "bran_max": 0.10}
    }
}

# --- 4. SIDEBAR & SEASONALITY ---
with st.sidebar:
    st.header("🚜 Farm Manager")
    lang = st.radio("Language:", ["English", "Kiswahili"])
    flock_type = st.radio("Select Type:", ["Broiler", "Layer"], key="flock_selector")
    
    # PRICE FLUCTUATION FACTOR
    season = st.select_slider("Market Season:", options=["Harvest (Cheap)", "Normal", "Dry (Expensive)"], value="Normal")
    price_multiplier = {"Harvest (Cheap)": 0.85, "Normal": 1.0, "Dry (Expensive)": 1.25}[season]

    t = {
        "English": {
            "dash": "📊 Dashboard", "solver": "🧪 LCR Optimizer", "guide": "📚 Guide", "market": "🛒 Market",
            "birds": "Live Birds", "age": "Age (Days)", "yield_meat": "Est. Yield (kg)", "roi_title": "💵 Profit Projection",
            "save_btn": "🚀 Save Today's Progress", "hist_title": "📋 Batch History"
        },
        "Kiswahili": {
            "dash": "📊 Dashibodi", "solver": "🧪 Kikokotoo LCR", "guide": "📚 Mwongozo", "market": "🛒 Soko",
            "birds": "Kuku Waliopo", "age": "Umri (Siku)", "yield_meat": "Mavuno (kg)", "roi_title": "💵 Makadirio ya Faida",
            "save_btn": "🚀 Hifadhi Taarifa", "hist_title": "📋 Kumbukumbu"
        }
    }
    txt = t[lang]
    menu = st.radio("GO TO:", [txt["dash"], txt["solver"], txt["guide"], txt["market"]])
    
    st.divider()
    flock_id = st.text_input("Flock ID", value="Batch-001")
    flock_size = st.number_input("Total Birds", min_value=1, value=100)
    mortality = st.number_input("Mortality", min_value=0, value=0)
    start_date = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=14))
    active_birds = max(0, flock_size - mortality)
    age_days = (datetime.date.today() - start_date).days

# --- 5. DASHBOARD PAGE ---
if menu == txt["dash"]:
    st.title(f"{txt['dash']}: {flock_id}")
    m1, m2, m3 = st.columns(3)
    m1.metric(txt["birds"], f"{active_birds}", f"-{mortality} Dead")
    m2.metric(txt["age"], f"{age_days} Days")
    m3.metric(txt["yield_meat"] if flock_type == "Broiler" else "Status", f"{active_birds * 2.2:.1f} kg" if flock_type == "Broiler" else "Active")

    st.divider()
    if flock_type == "Broiler":
        f_in = st.number_input("Total Feed Used (kg)", value=10.0)
        a_wt = st.number_input("Avg Weight (kg)", value=0.5)
        kpi_val = f_in / (active_birds * a_wt) if (active_birds * a_wt) > 0 else 0
        st.metric("FCR (Lower is Better)", f"{kpi_val:.2f}")
    else:
        eggs = st.number_input("Eggs Collected Today", value=50)
        kpi_val = (eggs / active_birds * 100) if active_birds > 0 else 0
        st.metric("Laying Rate (HDEP%)", f"{kpi_val:.1f}%")

    st.subheader(txt["roi_title"])
    c_price = st.number_input("Market Selling Price", value=8500)
    revenue = (active_birds * c_price) if flock_type == "Broiler" else (kpi_val * 300)
    # Estimate base costs + seasonal feed costs
    profit = revenue - (flock_size * 2200 * price_multiplier) 
    st.metric("Projected Profit", f"{profit:,.0f} TSH", delta=f"{season} prices")
    
    if st.button(txt["save_btn"], key="save_to_supabase_btn"):
        save_to_supabase(flock_type, flock_id, age_days, active_birds, kpi_val, profit)

    st.subheader(txt["hist_title"])
    if supabase: 
        try:
            response = supabase.table("farm_records").select("*").eq("flock_id", flock_id).order("created_at", desc=True).limit(5).execute()
            if response.data:
                st.dataframe(pd.DataFrame(response.data), use_container_width=True)
        except:
            st.info("Log will appear here after first sync.")

# --- 6. PERFORMANCE FEED SOLVER (DEBUGGED) ---
elif menu == txt["solver"]:
    st.title(f"🚀 {txt['solver']} ({flock_type})")
    stage = st.selectbox("Stage:", list(STANDARDS[flock_type].keys()))
    t_data = STANDARDS[flock_type][stage]
    total_kg = st.number_input("Total Feed to Make (kg)", value=100.0)

    # FIXED INCLUSIONS (Minerals & Safety)
    oil_pct = 0.02 if flock_type == "Broiler" else 0.01 
    premix_min_pct = 0.05 # DCP + Premix
    toxin_binder_pct = 0.02 # Toxin Binder Factor
    use_bsf = st.checkbox("Include BSF Larvae (Sustainable)", value=True)
    use_bran = st.checkbox("Include Maize Bran (Cost Saver)", value=True)

    bsf_pct = t_data["bsf_max"] if use_bsf else 0.0
    bran_pct = t_data["bran_max"] if use_bran else 0.0
    
    # CALCULATE REMAINING SPACE FOR MAIZE/SOYA
    rem_space = 1.0 - oil_pct - premix_min_pct - toxin_binder_pct - bsf_pct - bran_pct
    
    # TARGET PROTEIN ADJUSTMENT
    protein_from_fixed = (bsf_pct * ING_DATABASE["BSF Larvae"]["prot"]) + (bran_pct * ING_DATABASE["Maize Bran"]["prot"])
    target_p_needed = t_data["prot"] - protein_from_fixed
    
    m_p, s_p = ING_DATABASE["Maize"]["prot"], ING_DATABASE["Soya Meal"]["prot"]
    # Solver logic
    soya_ratio = ((target_p_needed / rem_space) - m_p) / (s_p - m_p)
    soya_ratio = max(0, min(1, soya_ratio)) # Clamping

    # Final Weights
    w_maize = total_kg * rem_space * (1 - soya_ratio)
    w_soya = total_kg * rem_space * soya_ratio
    w_bsf = total_kg * bsf_pct
    w_bran = total_kg * bran_pct
    w_oil = total_kg * oil_pct
    w_others = total_kg * (premix_min_pct + toxin_binder_pct)

    st.subheader("🥣 Mixing Table (Recipe)")
    recipe_df = pd.DataFrame({
        "Ingredient": ["Maize (Whole)", "Soya Meal", "BSF Larvae", "Maize Bran", "Vegetable Oil", "Premix & Toxin Binder"],
        "Amount (kg)": [round(w_maize, 1), round(w_soya, 1), round(w_bsf, 1), round(w_bran, 1), round(w_oil, 1), round(w_others, 1)],
        "Cost (TSH)": [
            round(w_maize * ING_DATABASE["Maize"]["price"] * price_multiplier),
            round(w_soya * ING_DATABASE["Soya Meal"]["price"] * price_multiplier),
            round(w_bsf * ING_DATABASE["BSF Larvae"]["price"]),
            round(w_bran * ING_DATABASE["Maize Bran"]["price"] * price_multiplier),
            round(w_oil * ING_DATABASE["Vegetable Oil"]["price"]),
            round(w_others * 2500) # Fixed cost for minerals
        ]
    })
    st.table(recipe_df)
    st.info(f"💡 Total Batch Cost: {recipe_df['Cost (TSH)'].sum():,.0f} TSH")

# --- 7. GUIDE & MARKET ---
elif menu == txt["guide"]:
    st.title(txt["guide"])
    sel = st.selectbox("Select Ingredient:", list(ING_DATABASE.keys()))
    st.write(f"Showing quality guide for {sel}...")

elif menu == txt["market"]:
    st.title(txt["market"])
    for name, info in ING_DATABASE.items():
        curr_p = round(info['price'] * price_multiplier)
        c1, c2, c3 = st.columns([2, 1, 1])
        c1.write(f"**{name}**")
        c2.write(f"{curr_p} TSH/kg")
        c3.link_button("Order", f"https://wa.me/255777744657?text=I%20want%20to%20order%20{name}")

st.divider()
st.caption(f"🚀 FeedConvo Pro | {season} Pricing Enabled")
