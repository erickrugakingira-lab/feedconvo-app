import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import os

# --- 1. GLOBAL CONFIGURATION ---
st.set_page_config(
    page_title="FeedConvo Pro", 
    layout="wide", 
    initial_sidebar_state="expanded", 
    page_icon="https://raw.githubusercontent.com/erickrugakingira-lab/feedconvo-app/main/assets/Main_logo.png"
)

# --- 2. THE DATABASES (UPGRADED FOR PERFORMANCE) ---
# Added: en (Energy), lys (Lysine), met (Methionine)
ING_DATABASE = {
    "Maize": {
        "img": "maize_grain.jpg", "prot": 9.0, "en": 3350, "lys": 0.24, "met": 0.18, "price_per_kg": 850,
        "qc": ["✅ Unyevu < 13% / Moisture < 13%", "✅ Nafaka nzima / Whole grains", "❌ **Red Flag:** Vumbi la kijani au jeusi (Aflatoxin)"]
    },
    "Soya Meal": {
        "img": "soyameal.jpg", "prot": 44.0, "en": 2500, "lys": 2.70, "met": 0.65, "price_per_kg": 2300,
        "qc": ["✅ Rangi ya dhahabu / Golden color", "✅ Harufu ya karanga / Roasted nutty smell", "❌ **Red Flag:** Harufu ya maharagwe mabichi"]
    },
    "BSF Larvae": {
        "img": "bsfl.jpg", "prot": 50.0, "en": 3100, "lys": 3.10, "met": 0.90, "price_per_kg": 1500,
        "qc": ["✅ Imekauka vizuri / Properly dried", "✅ Haina harufu kali / No foul smell", "🌱 **Eco-Friendly:** High protein"]
    },
    "Vegetable Oil": {
        "img": "vegetable-oil.webp", "prot": 0.0, "en": 8800, "lys": 0.0, "met": 0.0, "price_per_kg": 3500,
        "qc": ["✅ Rangi angavu / Clear color", "❌ **Red Flag:** Harufu mbaya"]
    },
    "Sunflower Cake": {
        "img": "sunflower_cake.jpeg", "prot": 28.0, "en": 2100, "lys": 0.90, "met": 0.50, "price_per_kg": 950,
        "qc": ["✅ Imekauka / Dry", "❌ **Red Flag:** Mafuta yanayovuja"]
    }
}

# Advanced Targets (Energy & Amino Acids)
STANDARDS = {
    "Broiler": {
        "Starter (Wk 1-2)": {"prot": 22.0, "en": 3000, "lys": 1.20, "bsf_max": 0.05},
        "Grower (Wk 3-4)": {"prot": 20.0, "en": 3100, "lys": 1.05, "bsf_max": 0.10},
        "Finisher (Wk 5+)": {"prot": 18.0, "en": 3200, "lys": 0.95, "bsf_max": 0.15}
    },
    "Layer": {
        "Chick Starter": {"prot": 18.0, "en": 2850, "lys": 0.85, "bsf_max": 0.05},
        "Pullet Grower": {"prot": 15.0, "en": 2750, "lys": 0.65, "bsf_max": 0.10},
        "Layer Phase 1": {"prot": 18.0, "en": 2800, "lys": 0.90, "bsf_max": 0.12}
    }
}

# --- 3. CLOUD CONNECTION ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    st.error("Google Sheets Connection Not Configured in Secrets.")

def save_to_google_sheets(flock_type, flock_name, age, birds, kpi_val, profit_val):
    try:
        existing_data = conn.read(ttl=0) 
        existing_data = existing_data.dropna(how="all")
        new_entry = pd.DataFrame([{
            "Date": datetime.date.today().strftime('%Y-%m-%d'),
            "Type": flock_type, "Flock_ID": flock_name, "Age": age,
            "Birds": birds, "KPI_Value": round(kpi_val, 2), "Profit_TSH": round(profit_val, 2)
        }])
        updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
        
        # Update the sheet
        conn.update(data=updated_df)
        st.success(f"☁️ Cloud Sync Successful for {flock_name}!")
    except Exception as e:
        st.error(f"Cloud Sync Failed: {e}")

# --- 4. STYLING & SIDEBAR ---
selected_type = st.session_state.get("flock_selector", "Broiler")
bg_url = "https://raw.githubusercontent.com/erickrugakingira-lab/feedconvo-app/main/broiler_chicken.png" if selected_type == "Broiler" else "https://raw.githubusercontent.com/erickrugakingira-lab/feedconvo-app/main/assets/layers.webp"

st.markdown(f"""<style>.stApp {{ background: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url("{bg_url}"); background-attachment: fixed; background-size: 40%; background-repeat: no-repeat; background-position: center bottom; }} h1, h2, h3 {{ color: #1b5e20; }}</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.header("🚜 Farm Manager")
    lang = st.radio("Language:", ["English", "Kiswahili"])
    flock_type = st.radio("Select Type:", ["Broiler", "Layer"], key="flock_selector")
    
    t = {
        "English": {
            "dash": "📊 Dashboard", "solver": "🧪 LCR Optimizer", "guide": "📚 Guide", "market": "🛒 Market",
            "birds": "Live Birds", "age": "Age (Days)", "yield_meat": "Est. Yield (kg)", "roi_title": "💵 Profit Projection",
            "save_btn": "🚀 Save Today's Progress", "hist_title": "📋 Batch History", "mixing": "🥣 Instructions"
        },
        "Kiswahili": {
            "dash": "📊 Dashibodi", "solver": "🧪 Kikokotoo LCR", "guide": "📚 Mwongozo", "market": "🛒 Soko",
            "birds": "Kuku Waliopo", "age": "Umri (Siku)", "yield_meat": "Mavuno (kg)", "roi_title": "💵 Makadirio ya Faida",
            "save_btn": "🚀 Hifadhi Taarifa", "hist_title": "📋 Kumbukumbu", "mixing": "🥣 Maelekezo"
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
    # Simplified KPI Logic
    if flock_type == "Broiler":
        f_in = st.number_input("Total Feed Used (kg)", value=10.0)
        a_wt = st.number_input("Avg Weight (kg)", value=0.5)
        kpi_val = f_in / (active_birds * a_wt) if (active_birds * a_wt) > 0 else 0
        st.metric("FCR (Lower is Better)", f"{kpi_val:.2f}")
    else:
        eggs = st.number_input("Eggs Collected Today", value=50)
        kpi_val = (eggs / active_birds * 100) if active_birds > 0 else 0
        st.metric("Laying Rate (HDEP%)", f"{kpi_val:.1f}%")

    # Financials
    st.subheader(txt["roi_title"])
    c_price = st.number_input("Market Selling Price", value=8500)
    revenue = (active_birds * c_price) if flock_type == "Broiler" else (kpi_val * 300)
    profit = revenue - (flock_size * 2000) # Simple estimation
    
    st.metric("Projected Profit", f"{profit:,.0f} TSH")
    
    if st.button(txt["save_btn"]):
        save_to_google_sheets(flock_type, flock_id, age_days, active_birds, kpi_val, profit)

    st.subheader(txt["hist_title"])
    try:
        df = conn.read(worksheet="Sheet1").dropna(how="all")
        st.dataframe(df[df['Type'] == flock_type], use_container_width=True)
    except:
        st.info("History will appear after your first save.")

# --- 6. PERFORMANCE FEED SOLVER ---
elif menu == txt["solver"]:
    st.title(f"🚀 {txt['solver']} ({flock_type})")
    stage = st.selectbox("Stage:", list(STANDARDS[flock_type].keys()))
    t_data = STANDARDS[flock_type][stage]
    total_kg = st.number_input("Total Feed to Make (kg)", value=100.0)

    # 1. Performance Logic: Automatic Energy Boost
    oil_pct = 0.02 if flock_type == "Broiler" else 0.01 
    premix_min_pct = 0.07 # Premix + DCP
    
    # 2. BSFL Safety Guardrail
    use_bsf = st.checkbox(f"Use BSFL (Auto-capped at {t_data['bsf_max']*100}% for this age)", value=True)
    bsf_pct = t_data["bsf_max"] if use_bsf else 0.0
    
    # 3. Solver Math
    rem_space = 1.0 - oil_pct - premix_min_pct - bsf_pct
    target_p = t_data["prot"] - (bsf_pct * ING_DATABASE["BSF Larvae"]["prot"])
    
    m_p, s_p = ING_DATABASE["Maize"]["prot"], ING_DATABASE["Soya Meal"]["prot"]
    soya_ratio = ((target_p / rem_space) - m_p) / (s_p - m_p)
    
    # Weights
    w_maize = total_kg * rem_space * (1 - soya_ratio)
    w_soya = total_kg * rem_space * soya_ratio
    w_bsf = total_kg * bsf_pct
    w_oil = total_kg * oil_pct
    w_other = total_kg * premix_min_pct

    # Amino Acid Check
    calc_lys = ((w_maize/total_kg)*ING_DATABASE["Maize"]["lys"] + (w_soya/total_kg)*ING_DATABASE["Soya Meal"]["lys"] + (w_bsf/total_kg)*ING_DATABASE["BSF Larvae"]["lys"]) * 100

    st.subheader("🥣 Mixing Table")
    recipe_df = pd.DataFrame({
        "Ingredient": ["Maize", "Soya Meal", "BSF Larvae", "Vegetable Oil", "Premix/DCP"],
        "Amount (kg)": [round(w_maize, 1), round(w_soya, 1), round(w_bsf, 1), round(w_oil, 1), round(w_other, 1)]
    })
    st.table(recipe_df)
    
    # Performance Insight
    c1, c2 = st.columns(2)
    c1.metric("Target Energy", f"{t_data['en']} kcal")
    c2.metric("Lysine Content", f"{calc_lys:.2f}%", delta="Optimal" if calc_lys >= t_data["lys"] else "Low")
    
    if calc_lys < t_data["lys"]:
        st.warning("⚠️ For maximum growth, consider adding 200g of Lysine powder to this mix.")

# --- 7. GUIDE & MARKET ---
elif menu == txt["guide"]:
    st.title(txt["guide"])
    sel = st.selectbox("Select Ingredient:", list(ING_DATABASE.keys()))
    st.image(f"https://raw.githubusercontent.com/erickrugakingira-lab/feedconvo-app/main/assets/{ING_DATABASE[sel]['img']}")
    for q in ING_DATABASE[sel]["qc"]: st.write(q)

elif menu == txt["market"]:
    st.title(txt["market"])
    for name, info in ING_DATABASE.items():
        c1, c2, c3 = st.columns([2, 1, 1])
        c1.write(f"**{name}**")
        c2.write(f"{info['price_per_kg']} TSH/kg")
        c3.link_button("Order", f"https://wa.me/255700000000?text=I%20want%20to%20order%20{name}")

st.divider()
st.caption("🚀 FeedConvo Pro | Performance Mode Active | Cloud Synced")
