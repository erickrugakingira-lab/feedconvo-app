import streamlit as st
import pandas as pd
import datetime
import os
from google.cloud import firestore
from google.oauth2 import service_account

# --- 1. GLOBAL CONFIGURATION ---
st.set_page_config(
    page_title="FeedConvo Pro", 
    layout="wide", 
    initial_sidebar_state="expanded", 
    page_icon="https://raw.githubusercontent.com/erickrugakingira-lab/feedconvo-app/main/assets/Main_logo.png"
)

# --- 3. FIREBASE CONNECTION ---
@st.cache_resource
def get_db():
    try:
        # 1. Pull the secrets
        key_dict = dict(st.secrets["firebase"])
        
        # 2. THE CLEANER: This removes "extra data" causing the ASN.1 error
        raw_key = key_dict["private_key"]
        
        # Fix: Remove literal '\n' strings if they exist
        clean_key = raw_key.replace("\\n", "\n")
        
        # Fix: Strip any invisible spaces/newlines from the start and end
        clean_key = clean_key.strip()
        
        # Re-insert the cleaned key into the dictionary
        key_dict["private_key"] = clean_key
        
        # 3. Connect
        creds = service_account.Credentials.from_service_account_info(key_dict)
        return firestore.Client(credentials=creds, project=key_dict["project_id"])
    except Exception as e:
        st.error("🔒 Security Key Handshake Failed")
        st.exception(e)
        return None

db = get_db()

def save_to_firebase(flock_type, flock_name, age, birds, kpi_val, profit_val):
    if db:
        try:
            # Creating a record entry
            record_ref = db.collection("farm_records").document() # Auto-generates unique ID
            record_ref.set({
                "Date": datetime.date.today().strftime('%Y-%m-%d'),
                "Type": flock_type,
                "Flock_ID": flock_name,
                "Age": age,
                "Birds": birds,
                "KPI_Value": round(kpi_val, 2),
                "Profit_TSH": round(profit_val, 2),
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            st.success(f"🔥 Firebase Sync Successful for {flock_name}!")
        except Exception as e:
            st.error(f"🔥 Firebase Sync Failed: {e}")

# --- 3. THE DATABASES ---
ING_DATABASE = {
    "Maize": {
        "img": "maize_grain.jpg", "prot": 9.0, "en": 3350, "lys": 0.24, "met": 0.18, "price_per_kg": 850,
        "qc": ["✅ Unyevu < 13%", "✅ Nafaka nzima", "❌ Red Flag: Aflatoxin"]
    },
    "Soya Meal": {
        "img": "soyameal.jpg", "prot": 44.0, "en": 2500, "lys": 2.70, "met": 0.65, "price_per_kg": 2300,
        "qc": ["✅ Rangi ya dhahabu", "✅ Harufu ya karanga", "❌ Red Flag: Harufu ya maharagwe mabichi"]
    },
    "BSF Larvae": {
        "img": "bsfl.jpg", "prot": 50.0, "en": 3100, "lys": 3.10, "met": 0.90, "price_per_kg": 1500,
        "qc": ["✅ Imekauka vizuri", "✅ Haina harufu kali", "🌱 Eco-Friendly"]
    },
    "Vegetable Oil": {
        "img": "vegetable-oil.webp", "prot": 0.0, "en": 8800, "lys": 0.0, "met": 0.0, "price_per_kg": 3500,
        "qc": ["✅ Rangi angavu", "❌ Red Flag: Harufu mbaya"]
    },
    "Sunflower Cake": {
        "img": "sunflower_cake.jpeg", "prot": 28.0, "en": 2100, "lys": 0.90, "met": 0.50, "price_per_kg": 950,
        "qc": ["✅ Imekauka", "❌ Red Flag: Mafuta yanayovuja"]
    }
}

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

# --- 4. STYLING & SIDEBAR ---
selected_type = st.session_state.get("flock_selector", "Broiler")
bg_url = "https://raw.githubusercontent.com/erickrugakingira-lab/feedconvo-app/main/broiler_chicken.png" if selected_type == "Broiler" else "https://raw.githubusercontent.com/erickrugakingira-lab/feedconvo-app/main/assets/layers.webp"

st.markdown(f"""<style>.stApp {{ background: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url("{bg_url}"); background-attachment: fixed; background-size: 40%; background-repeat: no-repeat; background-position: center bottom; }}</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.header("🚜 Farm Manager")
    lang = st.radio("Language:", ["English", "Kiswahili"])
    flock_type = st.radio("Select Type:", ["Broiler", "Layer"], key="flock_selector")
    
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
    profit = revenue - (flock_size * 2000) 
    st.metric("Projected Profit", f"{profit:,.0f} TSH")
    
    if st.button(txt["save_btn"]):
        save_to_firebase(flock_type, flock_id, age_days, active_birds, kpi_val, profit)

    st.subheader(txt["hist_title"])
    if db:
        try:
            # Query Firebase for recent logs
            docs = db.collection("farm_records").where("Flock_ID", "==", flock_id).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(10).stream()
            hist_data = [d.to_dict() for d in docs]
            if hist_data:
                st.dataframe(pd.DataFrame(hist_data), use_container_width=True)
            else:
                st.info("No records found for this flock yet.")
        except Exception as e:
            st.info("Record log will appear here after your first save.")

# --- 6. PERFORMANCE FEED SOLVER ---
elif menu == txt["solver"]:
    st.title(f"🚀 {txt['solver']} ({flock_type})")
    stage = st.selectbox("Stage:", list(STANDARDS[flock_type].keys()))
    t_data = STANDARDS[flock_type][stage]
    total_kg = st.number_input("Total Feed to Make (kg)", value=100.0)

    oil_pct = 0.02 if flock_type == "Broiler" else 0.01 
    premix_min_pct = 0.07 
    use_bsf = st.checkbox(f"Use BSFL (Auto-capped at {t_data['bsf_max']*100}%)", value=True)
    bsf_pct = t_data["bsf_max"] if use_bsf else 0.0
    
    rem_space = 1.0 - oil_pct - premix_min_pct - bsf_pct
    target_p = t_data["prot"] - (bsf_pct * ING_DATABASE["BSF Larvae"]["prot"])
    m_p, s_p = ING_DATABASE["Maize"]["prot"], ING_DATABASE["Soya Meal"]["prot"]
    soya_ratio = ((target_p / rem_space) - m_p) / (s_p - m_p)
    
    w_maize = total_kg * rem_space * (1 - soya_ratio)
    w_soya = total_kg * rem_space * soya_ratio
    w_bsf = total_kg * bsf_pct
    w_oil = total_kg * oil_pct
    w_other = total_kg * premix_min_pct

    st.subheader("🥣 Mixing Table")
    recipe_df = pd.DataFrame({
        "Ingredient": ["Maize", "Soya Meal", "BSF Larvae", "Vegetable Oil", "Premix/DCP"],
        "Amount (kg)": [round(w_maize, 1), round(w_soya, 1), round(w_bsf, 1), round(w_oil, 1), round(w_other, 1)]
    })
    st.table(recipe_df)

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
st.caption("🚀 FeedConvo Pro | Powered by Firebase Firestore")
