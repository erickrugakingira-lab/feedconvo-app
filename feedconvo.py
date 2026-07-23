import streamlit as st
import pandas as pd
import datetime
from scipy.optimize import linprog
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

def save_to_supabase(flock_type, flock_id, age, birds, kpi_val, profit_val, is_market_listed=False, market_region="", market_district="", asking_price=0):
    if supabase:
        data = {
            "flock_type": str(flock_type),
            "flock_id": str(flock_id),
            "age_days": int(age),
            "active_birds": int(birds),
            "kpi_value": float(kpi_val),
            "profit_tsh": float(profit_val),
            "is_listed": bool(is_market_listed),
            "location_region": str(market_region),
            "location_district": str(market_district),
            "asking_price_tsh": float(asking_price)
        }
        try:
            supabase.table("farm_records").insert(data).execute()
            st.success(f"✅ Data Synced to Supabase for {flock_id}!")
        except Exception as e:
            st.error(f"❌ Supabase Insert Failed: {e}")

# --- 3. INGREDIENT DATABASE ---
# NOTE ON DATA BASIS (read before editing these numbers):
#   - "prot"        = total Crude Protein, % as-fed
#   - "en"          = Metabolizable Energy, kcal/kg as-fed
#   - "fiber"       = Crude Fiber, % as-fed (drives the new max-fiber constraint below)
#   - "dig_lys/met/tryp" = STANDARDIZED ILEAL DIGESTIBLE amino acids, % as-fed
#         (NOT total/crude AA — this is the fix for the "is it digestible or total AA"
#         question. These were derived as total_AA x published SID digestibility
#         coefficient for that ingredient class. Coefficients are drawn from peer-reviewed
#         ileal-digestibility trials in broilers/layers and are consistent with the
#         methodology used in Rostagno et al., "Tabelas Brasileiras para Aves e Suínos"
#         (digestible AA, non-phytate/available P) — but exact cell values from that
#         book are copyrighted and were not reproduced verbatim here. Cross-check
#         against your physical/PDF copy of the current edition before relying on
#         these for commercial-scale formulation.
#   - "avail_phos"  = available (non-phytate) phosphorus, % as-fed — NOT total P.
#         Plant ingredients typically have only ~25-35% of their total P available to
#         poultry (the rest is phytate-bound); animal-origin ingredients (fish meal) and
#         inorganic sources (DCP) are close to fully available.
#   - "ca"          = total Calcium, % as-fed (Ca digestibility corrections are not yet
#         applied here — a known simplification, flagged for future work)
#   - "max_incl"    = default realistic maximum inclusion rate (fraction of total feed)
#         based on published practical/anti-nutritional limits. Stage-specific caps
#         (Fish Meal, BSF Larvae, Vegetable Oil, Maize Bran, Rice Bran) are still pulled
#         from STANDARDS below because those genuinely vary by bird age.
if "ING_DATABASE" not in st.session_state:
    st.session_state["ING_DATABASE"] = {
        # --- Energy (ME) Sources ---
        "Maize":            {"prot": 8.0,  "en": 3300, "fiber": 2.2,  "dig_lys": 0.20, "dig_met": 0.15, "dig_tryp": 0.06, "ca": 0.02, "avail_phos": 0.08, "price": 850,  "type": "ME", "quality_score": 6,  "max_incl": 0.70},
        "Sorghum":          {"prot": 9.0,  "en": 3250, "fiber": 2.5,  "dig_lys": 0.18, "dig_met": 0.14, "dig_tryp": 0.07, "ca": 0.04, "avail_phos": 0.09, "price": 750,  "type": "ME", "quality_score": 5,  "max_incl": 0.30},
        "Dehulled Sorghum": {"prot": 9.5,  "en": 3300, "fiber": 1.8,  "dig_lys": 0.19, "dig_met": 0.15, "dig_tryp": 0.07, "ca": 0.03, "avail_phos": 0.09, "price": 850,  "type": "ME", "quality_score": 7,  "max_incl": 0.35},
        "Rice Bran":        {"prot": 13.5, "en": 2900, "fiber": 12.0, "dig_lys": 0.41, "dig_met": 0.17, "dig_tryp": 0.12, "ca": 0.08, "avail_phos": 0.20, "price": 500,  "type": "ME", "quality_score": 4,  "max_incl": 0.15},  # capped hard — see stage override below
        "Cassava Meal":     {"prot": 2.8,  "en": 3000, "fiber": 4.0,  "dig_lys": 0.06, "dig_met": 0.03, "dig_tryp": 0.02, "ca": 0.12, "avail_phos": 0.03, "price": 600,  "type": "ME", "quality_score": 2,  "max_incl": 0.20},  # requires proper sun-drying to reduce cyanogenic glycosides
        "Maize Bran":       {"prot": 9.4,  "en": 2200, "fiber": 8.0,  "dig_lys": 0.23, "dig_met": 0.11, "dig_tryp": 0.04, "ca": 0.03, "avail_phos": 0.15, "price": 450,  "type": "ME", "quality_score": 4,  "max_incl": 0.20},
        "Vegetable Oil":    {"prot": 0.0,  "en": 8800, "fiber": 0.0,  "dig_lys": 0.00, "dig_met": 0.00, "dig_tryp": 0.00, "ca": 0.00, "avail_phos": 0.00, "price": 3500, "type": "ME", "quality_score": 0,  "max_incl": 0.05},

        # --- Crude Protein Sources ---
        "Soya Meal":        {"prot": 43.0, "en": 2440, "fiber": 6.5,  "dig_lys": 2.43, "dig_met": 0.58, "dig_tryp": 0.54, "ca": 0.29, "avail_phos": 0.22, "price": 2300, "type": "CP", "quality_score": 10, "max_incl": 0.40},
        "Cotton Seed Cake": {"prot": 40.0, "en": 1700, "fiber": 15.0, "dig_lys": 1.05, "dig_met": 0.39, "dig_tryp": 0.31, "ca": 0.35, "avail_phos": 0.30, "price": 900,  "type": "CP", "quality_score": 5,  "max_incl": 0.10},  # gossypol — keep at/below 10%
        "Wheat Pollard":    {"prot": 15.0, "en": 2100, "fiber": 10.0, "dig_lys": 0.47, "dig_met": 0.17, "dig_tryp": 0.13, "ca": 0.10, "avail_phos": 0.20, "price": 650,  "type": "CP", "quality_score": 6,  "max_incl": 0.15},
        "Coconut Cake":     {"prot": 21.0, "en": 1650, "fiber": 13.0, "dig_lys": 0.44, "dig_met": 0.25, "dig_tryp": 0.14, "ca": 0.20, "avail_phos": 0.15, "price": 800,  "type": "CP", "quality_score": 5,  "max_incl": 0.10},
        "BSF Larvae":       {"prot": 50.0, "en": 3100, "fiber": 6.0,  "dig_lys": 2.48, "dig_met": 0.76, "dig_tryp": 0.49, "ca": 0.85, "avail_phos": 0.55, "price": 1500, "type": "CP", "quality_score": 9,  "max_incl": 0.15},  # chitin content limits digestibility & safe inclusion — stage override below
        "Fish Meal":        {"prot": 60.0, "en": 2600, "fiber": 0.0,  "dig_lys": 4.05, "dig_met": 1.66, "dig_tryp": 0.62, "ca": 4.80, "avail_phos": 2.40, "price": 2500, "type": "CP", "quality_score": 10, "max_incl": 0.15},  # stage override below

        # --- Macro Minerals ---
        "Limestone": {"prot": 0.0, "en": 0.0, "fiber": 0.0, "dig_lys": 0.0, "dig_met": 0.0, "dig_tryp": 0.0, "ca": 38.0, "avail_phos": 0.0,  "price": 300,  "type": "MIN", "quality_score": 0, "max_incl": 0.12},  # stage override below
        "DCP":       {"prot": 0.0, "en": 0.0, "fiber": 0.0, "dig_lys": 0.0, "dig_met": 0.0, "dig_tryp": 0.0, "ca": 21.0, "avail_phos": 17.0, "price": 1200, "type": "MIN", "quality_score": 0, "max_incl": 0.06},

        # --- Synthetic Amino Acids & Essentials (~99% digestible, treated as fully available) ---
        "DL-Methionine": {"prot": 58.0, "en": 0.0, "fiber": 0.0, "dig_lys": 0.0,  "dig_met": 98.0, "dig_tryp": 0.0, "ca": 0.0, "avail_phos": 0.0, "price": 9500, "type": "CP", "quality_score": 0, "max_incl": 0.01},
        "L-Lysine HCL":  {"prot": 94.0, "en": 0.0, "fiber": 0.0, "dig_lys": 78.0, "dig_met": 0.0,  "dig_tryp": 0.0, "ca": 0.0, "avail_phos": 0.0, "price": 7500, "type": "CP", "quality_score": 0, "max_incl": 0.01},
        "Salt":          {"prot": 0.0,  "en": 0.0, "fiber": 0.0, "dig_lys": 0.0,  "dig_met": 0.0,  "dig_tryp": 0.0, "ca": 0.0, "avail_phos": 0.0, "price": 400,  "type": "MIN", "quality_score": 0, "max_incl": 0.003}
    }

ING_DATABASE = st.session_state["ING_DATABASE"]

# STANDARDS now expressed on a DIGESTIBLE AA / AVAILABLE P basis (matches ING_DATABASE).
# Approximate figures consistent with published SID broiler/layer nutrient specs
# (Rostagno / Cobb-Vantress / Hy-Line style digestible requirement tables) — verify
# against your specific breed's current guide before locking these in for production.
# "max_fiber" and "rice_bran_max" are new constraints added to keep formulas practical.
STANDARDS = {
    # Broiler targets below are day-weighted blends derived directly from Rostagno et al.,
    # "Brazilian Tables for Poultry and Swine" 5th ed., for HIGH PERFORMANCE (commercial
    # hybrid: Cobb/Ross/Arbor Acres-type) genetics:
    #   - Starter (days 1-14): blended from Table 2.28 (thermoneutral) brackets 0-8 & 8-17,
    #     since chicks are under supplemental brooder heat during this window regardless
    #     of ambient climate.
    #   - Grower (days 15-28) & Finisher (days 29-49): blended from Table 2.29 (High
    #     Performance grown at 26°C average, 21-31°C range — i.e. tropical ambient
    #     conditions like Tanzania) brackets 8-17/17-27/27-35 and 27-35/35-43/43-49
    #     respectively, once chicks are off supplemental heat.
    # AA are standardized ileal digestible (SID); phosphorus is available (non-phytate) P.
    # min/max bands are a practical tolerance placed around Rostagno's single-point
    # targets, not a range Rostagno itself publishes. Crude fiber caps are NOT from
    # Rostagno (these tables don't cover fiber) — sourced separately, see Section 3 notes.
    "Broiler": {
        "Starter (Wk 1-2)": {
            "min_cp": 23.2, "max_cp": 24.2, "min_en": 2950, "max_en": 3020,
            "min_lys": 1.28, "max_lys": 1.38, "min_met": 0.51, "max_met": 0.56,
            "min_tryp": 0.22, "max_tryp": 0.26, "min_ca": 1.05, "min_phos": 0.50,
            "bsf_max": 0.05, "bran_max": 0.03, "oil_max": 0.03, "rice_bran_max": 0.08,
            "max_fiber": 4.0, "min_pqi": 7.6
        },
        "Grower (Wk 3-4)": {
            "min_cp": 22.6, "max_cp": 23.6, "min_en": 3020, "max_en": 3090,
            "min_lys": 1.24, "max_lys": 1.34, "min_met": 0.51, "max_met": 0.56,
            "min_tryp": 0.21, "max_tryp": 0.25, "min_ca": 0.79, "min_phos": 0.37,
            "bsf_max": 0.10, "bran_max": 0.08, "oil_max": 0.04, "rice_bran_max": 0.12,
            "max_fiber": 5.0, "min_pqi": 6.9
        },
        "Finisher (Wk 5+)": {
            "min_cp": 22.2, "max_cp": 23.2, "min_en": 3080, "max_en": 3150,
            "min_lys": 1.21, "max_lys": 1.31, "min_met": 0.50, "max_met": 0.55,
            "min_tryp": 0.20, "max_tryp": 0.24, "min_ca": 0.68, "min_phos": 0.32,
            "bsf_max": 0.15, "bran_max": 0.12, "oil_max": 0.05, "rice_bran_max": 0.15,
            "max_fiber": 6.0, "min_pqi": 6.4
        }
    },
    # Layer targets derived from Rostagno et al. 5th ed.:
    #   - Chick Starter (1-4wk) & Pre-Lay (16-18wk): taken directly from Table 3.13,
    #     "Brown Replacement Pullets" (commercial layer-bound pullets — NOT the Broiler
    #     Breeder Pullet table, which is a different bird purpose entirely).
    #   - Pullet Grower (5-15wk): day-weighted blend of Table 3.13's Grower (5-10wk,
    #     6 weeks) and Development (11-15wk, 5 weeks) columns.
    #   - Layer Phase 1 (production): weighted blend of Table 3.37's three production-
    #     phase columns (Standard Performance Brown Layers) using an assumed ~45/32/23%
    #     split across a typical laying cycle (peak/mid/late lay) — this is a reasonable
    #     industry-standard duration split, NOT a figure Rostagno publishes directly.
    #     Revisit if you split Layer Phase 1 into 3 separate stages later.
    # AA are SID (standardized ileal digestible); phosphorus is available (non-phytate) P.
    # Note the Calcium jump into Pre-Lay (1.25%+) — deliberate, builds medullary bone Ca
    # reserves before eggshell formation begins. Don't shorten or blend this phase away.
    "Layer": {
        "Chick Starter": {
            "min_cp": 17.3, "max_cp": 18.3, "min_en": 2820, "max_en": 2880,
            "min_lys": 0.94, "max_lys": 1.02, "min_met": 0.37, "max_met": 0.42,
            "min_tryp": 0.16, "max_tryp": 0.19, "min_ca": 1.08, "min_phos": 0.39,
            "bsf_max": 0.05, "bran_max": 0.05, "oil_max": 0.02, "rice_bran_max": 0.08,
            "max_fiber": 5.0, "min_pqi": 7.4
        },
        "Pullet Grower": {
            "min_cp": 12.6, "max_cp": 13.4, "min_en": 2820, "max_en": 2880,
            "min_lys": 0.68, "max_lys": 0.74, "min_met": 0.29, "max_met": 0.33,
            "min_tryp": 0.13, "max_tryp": 0.16, "min_ca": 0.83, "min_phos": 0.31,
            "bsf_max": 0.10, "bran_max": 0.20, "oil_max": 0.02, "rice_bran_max": 0.15,
            "max_fiber": 7.0, "min_pqi": 6.6
        },
        "Pre-Lay": {
            "min_cp": 15.1, "max_cp": 16.1, "min_en": 2820, "max_en": 2880,
            "min_lys": 0.80, "max_lys": 0.87, "min_met": 0.36, "max_met": 0.41,
            "min_tryp": 0.16, "max_tryp": 0.19, "min_ca": 1.26, "min_phos": 0.24,
            "bsf_max": 0.10, "bran_max": 0.15, "oil_max": 0.03, "rice_bran_max": 0.15,
            "max_fiber": 6.0, "min_pqi": 6.9
        },
        "Layer Phase 1": {
            "min_cp": 13.4, "max_cp": 14.2, "min_en": 2820, "max_en": 2880,
            "min_lys": 0.67, "max_lys": 0.73, "min_met": 0.30, "max_met": 0.35,
            "min_tryp": 0.15, "max_tryp": 0.18, "min_ca": 3.55, "min_phos": 0.21,
            "bsf_max": 0.12, "bran_max": 0.10, "oil_max": 0.03, "rice_bran_max": 0.15,
            "max_fiber": 7.0, "min_pqi": 7.0
        }
    }
}

# --- 4. LAYER ROUTER ---
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None

if st.session_state["user_role"] is None:
    st.title("🚜 Welcome to FeedConvo Pro")
    st.subheader("Linking Intelligent Production with Local Dynamic Markets")
    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.info("### 👨‍🌾 Poultry Farmer Portal\nFormulate least-cost rations, manage flocks, and broadcast inventory.")
        if st.button("Access Farmer Framework", use_container_width=True):
            st.session_state["user_role"] = "Farmer"
            st.rerun()
    with col_b:
        st.success("### 🛒 Trader & Buyer Directory\nAccess localized agricultural metrics and dynamic demands.")
        if st.button("Access Market/Trader Hub", use_container_width=True):
            st.session_state["user_role"] = "Trader"
            st.rerun()
    st.stop()

# -----------------------------------------------------------------------------
# WORKSPACE LAYER A: POULTRY FARMER WORKFLOW
# -----------------------------------------------------------------------------
if st.session_state["user_role"] == "Farmer":
    with st.sidebar:
        st.header("🚜 Farm Manager")
        if st.button("🔄 Switch to Buyer Layer", type="secondary"):
            st.session_state["user_role"] = None
            st.rerun()
            
        lang = st.radio("Language:", ["English", "Kiswahili"])
        flock_type = st.radio("Select Type:", ["Broiler", "Layer"], key="flock_selector")
        form_mode = st.selectbox("Formulation Mode:", ["Standard", "Premium", "Custom Eco"])
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
            f_in = st.number_input("Total Feed Consumed to Date (kg)", value=100.0, min_value=0.1)
            a_wt = st.number_input("Current Avg Body Weight (kg)", value=0.5, min_value=0.05)
            
            chick_start_weight = 0.04
            weight_gain = max(0.01, a_wt - chick_start_weight)
            kpi_val = f_in / (active_birds * weight_gain) if (active_birds * weight_gain) > 0 else 0
            st.metric("Feed Conversion Ratio (FCR based on Weight Gain)", f"{kpi_val:.2f}")
        else:
            eggs = st.number_input("Eggs Collected Today", value=50)
            kpi_val = (eggs / active_birds * 100) if active_birds > 0 else 0
            st.metric("Laying Rate (HDEP%)", f"{kpi_val:.1f}%")

        st.subheader(txt["roi_title"])
        c_price = st.number_input("Market Selling Price", value=8500)
        revenue = (active_birds * c_price) if flock_type == "Broiler" else (kpi_val * 300)
        profit = revenue - (flock_size * 2200 * price_multiplier) 
        st.metric("Projected Profit", f"{profit:,.0f} TSH", delta=f"{season} prices")
        
        st.markdown("---")
        st.subheader("📢 FeedConvo Marketplace Integration Gateway")
        gate_age_passed = age_days >= 28
        
        st.markdown("#### 🩺 Biosecurity & Vaccination Checklist")
        gumboro_checked = st.checkbox("Gumboro Vaccine Schedule Administered Completely", value=False)
        newcastle_checked = st.checkbox("Newcastle Vaccine Schedule Administered Completely", value=False)
        gate_vaccinations_passed = gumboro_checked and newcastle_checked
        
        is_market_listed = False
        market_region = ""
        market_district = ""
        asking_price = 0
        
        if gate_age_passed and gate_vaccinations_passed:
            st.success("✅ Verification Passed: This flock qualifies to be listed on the dynamic trader index.")
            is_market_listed = st.checkbox("Broadcast this flock to verified buyers & local traders anonymously", value=False)
            if is_market_listed:
                c_m1, c_m2, c_m3 = st.columns(3)
                with c_m1:
                    market_region = st.selectbox("Target Region:", ["Dar es Salaam", "Pwani", "Morogoro", "Arusha"])
                with c_m2:
                    market_district = st.text_input("District Name:", value="Ilala")
                with c_m3:
                    asking_price = st.number_input("Desired Asking Price per Bird (TSH):", value=int(c_price))
                st.info(f"💡 Publicly Listing: {active_birds} birds available in local district market index.")
        else:
            st.warning("🔒 Marketplace Broadcasting Locked")
            if not gate_age_passed:
                st.write(f"• Birds must reach threshold age of 28 Days (Current: {age_days} Days).")
            if not gate_vaccinations_passed:
                st.write("• Full biosecurity protection required: Check both core vaccination schedules.")
        
        st.markdown("---")
        if st.button(txt["save_btn"], key="save_to_supabase_btn"):
            save_to_supabase(flock_type, flock_id, age_days, active_birds, kpi_val, profit, is_market_listed, market_region, market_district, asking_price)

        st.subheader(txt["hist_title"])
        if supabase: 
            try:
                response = supabase.table("farm_records").select("*").eq("flock_id", flock_id).order("created_at", desc=True).limit(5).execute()
                if response.data:
                    st.dataframe(pd.DataFrame(response.data), use_container_width=True)
            except:
                st.info("Log will appear here after sync connection parameters match backend tables.")

    # --- 6. LEAST-COST RATION FEED SOLVER ---
    elif menu == txt["solver"]:
        st.title(f"🚀 {txt['solver']} ({flock_type}) — Least Cost Optimization")
        st.caption("Amino acid targets are on a **standardized ileal digestible (SID)** basis; phosphorus is **available P**, not total P.")

        stage = st.selectbox("Stage:", list(STANDARDS[flock_type].keys()))
        t_data = STANDARDS[flock_type][stage].copy()

        if form_mode == "Premium":
            t_data["min_cp"] += 0.5
            t_data["min_lys"] += 0.05

        total_kg = st.number_input("Total Feed to Make (kg)", value=100.0)

        st.sidebar.markdown("### 🥣 Select Ingredients")
        available_ingredients = st.sidebar.multiselect(
            "Choose Ingredients for Optimization",
            list(ING_DATABASE.keys()),
            default=["Maize", "Soya Meal", "Fish Meal", "Rice Bran", "Limestone", "DCP", "DL-Methionine", "L-Lysine HCL", "Salt"]
        )

        if len(available_ingredients) < 2:
            st.warning("Please select at least 2 macro ingredients to begin solving.")
            st.stop()

        # INGREDIENT BOUNDARY POLICY: realistic default max caps now live on each
        # ingredient itself (ING_DATABASE["max_incl"]) so nothing silently falls back
        # to an oversized ceiling. A few genuinely age-dependent ingredients are
        # overridden per stage from STANDARDS.
        STAGE_OVERRIDES = {
            "Limestone": (0.00, 0.12 if flock_type == "Layer" else 0.06),
            "Fish Meal": (0.00, 0.15 if "Starter" in stage else 0.12),
            "DL-Methionine": (0.00, 0.01 if "Starter" in stage else 0.005),
            "L-Lysine HCL": (0.00, 0.01 if "Starter" in stage else 0.005),
            "Salt": (0.003, 0.003),
            "BSF Larvae": (0.00, t_data.get("bsf_max", 0.15)),
            "Maize Bran": (0.00, t_data.get("bran_max", 0.12)),
            "Vegetable Oil": (0.00, t_data.get("oil_max", 0.05)),
            "Rice Bran": (0.00, t_data.get("rice_bran_max", 0.12)),
        }

        premix_pct = 0.005
        toxin_binder_pct = 0.001
        fixed_micro_pct = premix_pct + toxin_binder_pct
        remaining_pct = 1.0 - fixed_micro_pct

        FIXED_PRICE_INGREDIENTS = ["Limestone", "DCP", "DL-Methionine", "L-Lysine HCL", "Salt"]

        ingredient_names = []
        c = []
        protein_vals, energy_vals, fiber_vals = [], [], []
        lys_vals, met_vals, tryp_vals, ca_vals, phos_vals = [], [], [], [], []
        bounds = []

        for ing in available_ingredients:
            ingredient_names.append(ing)
            ing_data = ING_DATABASE[ing]

            ing_price = ing_data["price"] if ing in FIXED_PRICE_INGREDIENTS else ing_data["price"] * price_multiplier
            c.append(ing_price)

            protein_vals.append(ing_data["prot"])
            energy_vals.append(ing_data["en"])
            fiber_vals.append(ing_data["fiber"])
            lys_vals.append(ing_data["dig_lys"])
            met_vals.append(ing_data["dig_met"])
            tryp_vals.append(ing_data["dig_tryp"])
            ca_vals.append(ing_data["ca"])
            phos_vals.append(ing_data["avail_phos"])

            if ing in STAGE_OVERRIDES:
                bounds.append(STAGE_OVERRIDES[ing])
            else:
                # Falls back to the ingredient's own documented realistic cap —
                # NOT a blind 0.65 ceiling anymore.
                bounds.append((0.00, ing_data.get("max_incl", 0.20)))

        num_ingredients = len(ingredient_names)

        # Build constraints as (label, row, bound) so diagnostics below can reference
        # them by name instead of fragile positional indices.
        constraints = [
            ("Protein Deficit (min CP)",       [-p for p in protein_vals], -t_data["min_cp"]),
            ("Protein Excess (max CP)",        [p for p in protein_vals],   t_data["max_cp"]),
            ("Energy Deficit (min ME)",        [-e for e in energy_vals],  -t_data["min_en"]),
            ("Energy Excess (max ME)",         [e for e in energy_vals],    t_data["max_en"]),
            ("Digestible Lysine Shortage",     [-l for l in lys_vals],     -t_data["min_lys"]),
            ("Digestible Lysine Excess",       [l for l in lys_vals],       t_data["max_lys"]),
            ("Digestible Methionine Shortage", [-m for m in met_vals],     -t_data["min_met"]),
            ("Digestible Methionine Excess",   [m for m in met_vals],       t_data["max_met"]),
            ("Digestible Tryptophan Shortage", [-tv for tv in tryp_vals],  -t_data["min_tryp"]),
            ("Digestible Tryptophan Excess",   [tv for tv in tryp_vals],    t_data["max_tryp"]),
            ("Calcium Deficit",                [-ca for ca in ca_vals],    -t_data["min_ca"]),
            ("Available Phosphorus Deficit",   [-ph for ph in phos_vals],  -t_data["min_phos"]),
            ("Crude Fiber Excess",             [f for f in fiber_vals],     t_data["max_fiber"]),
        ]

        # Conditional Sorghum Energy Ratio constraint
        energy_ingredients = ["Maize", "Sorghum", "Dehulled Sorghum", "Maize Bran", "Wheat Pollard", "Cassava Meal"]
        has_sorghum = "Sorghum" in ingredient_names or "Dehulled Sorghum" in ingredient_names
        if has_sorghum:
            ratio_row = []
            for ing in ingredient_names:
                if ing in ["Sorghum", "Dehulled Sorghum"]:
                    ratio_row.append(0.50)
                elif ing in energy_ingredients:
                    ratio_row.append(-0.50)
                else:
                    ratio_row.append(0.00)
            constraints.append(("Sorghum Energy Ratio Deficit", ratio_row, 0.00))

        A_ub = [row for _, row, _ in constraints]
        b_ub = [bound for _, _, bound in constraints]
        constraint_labels = [label for label, _, _ in constraints]

        A_eq = [[1.0] * num_ingredients]
        b_eq = [remaining_pct]

        res = linprog(c=c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")

        if res.success:
            solution = res.x
            recipe_rows = []
            total_cost = 0
            audit_cp = audit_energy = audit_fiber = audit_lys = audit_met = audit_tryp = audit_ca = audit_phos = audit_pqi = 0.0

            for i, ing in enumerate(ingredient_names):
                inclusion_pct = solution[i]
                weight_kg = inclusion_pct * total_kg
                ing_price = ING_DATABASE[ing]["price"] * price_multiplier if ing not in FIXED_PRICE_INGREDIENTS else ING_DATABASE[ing]["price"]
                cost = weight_kg * ing_price
                
                total_cost += cost
                audit_cp += inclusion_pct * ING_DATABASE[ing]["prot"]
                audit_energy += inclusion_pct * ING_DATABASE[ing]["en"]
                audit_fiber += inclusion_pct * ING_DATABASE[ing]["fiber"]
                audit_lys += inclusion_pct * ING_DATABASE[ing]["dig_lys"]
                audit_met += inclusion_pct * ING_DATABASE[ing]["dig_met"]
                audit_tryp += inclusion_pct * ING_DATABASE[ing]["dig_tryp"]
                audit_ca += inclusion_pct * ING_DATABASE[ing]["ca"]
                audit_phos += inclusion_pct * ING_DATABASE[ing]["avail_phos"]
                audit_pqi += inclusion_pct * ING_DATABASE[ing].get("quality_score", 0)

                # Ingredients the optimizer picked at ~0% aren't part of the actual
                # recipe — skip them so the table only shows what the farmer needs to buy.
                if round(inclusion_pct * 100, 2) <= 0:
                    continue

                recipe_rows.append({
                    "Ingredient": ing,
                    "Inclusion %": round(inclusion_pct * 100, 2),
                    "Amount (kg)": round(weight_kg, 2),
                    "Cost (TSH)": round(cost)
                })

            premix_weight = premix_pct * total_kg
            toxin_weight = toxin_binder_pct * total_kg
            total_cost += (premix_weight * 2500) + (toxin_weight * 4000)

            recipe_rows.append({"Ingredient": "Premix", "Inclusion %": round(premix_pct * 100, 2), "Amount (kg)": round(premix_weight, 2), "Cost (TSH)": round(premix_weight * 2500)})
            recipe_rows.append({"Ingredient": "Toxin Binder", "Inclusion %": round(toxin_binder_pct * 100, 2), "Amount (kg)": round(toxin_weight, 2), "Cost (TSH)": round(toxin_weight * 4000)})

            recipe_df = pd.DataFrame(recipe_rows)
            st.subheader("🥣 Optimized Least-Cost Feed Formula")
            st.dataframe(recipe_df, use_container_width=True)

            st.markdown("### 📊 Nutritional Analysis Audit Summary")
            m_c1, m_c2, m_c3 = st.columns(3)
            m_c1.metric("Feed Cost Per Kg", f"{total_cost / total_kg:,.0f} TSH/kg")
            m_c2.metric("CP / ME Profiles", f"{audit_cp:.1f}% CP | {audit_energy:.0f} kcal")
            ca_phos_ratio = audit_ca / audit_phos if audit_phos > 0 else 0
            m_c3.metric("Ca : Available P Ratio", f"{ca_phos_ratio:.2f} : 1")

            aud1, aud2, aud3, aud4 = st.columns(4)
            if t_data["min_cp"] <= audit_cp <= t_data["max_cp"]:
                aud1.success(f"Crude Protein: {audit_cp:.2f}% (Safe)")
            else:
                aud1.warning(f"Crude Protein Out of Bounds: {audit_cp:.2f}%")

            if t_data["min_en"] <= audit_energy <= t_data["max_en"]:
                aud2.success(f"Energy: {audit_energy:.0f} kcal/kg (Safe)")
            else:
                aud2.warning(f"Energy Out of Bounds: {audit_energy:.0f} kcal")

            if audit_fiber <= t_data["max_fiber"]:
                aud3.success(f"Crude Fiber: {audit_fiber:.2f}% (Safe, ≤{t_data['max_fiber']}%)")
            else:
                aud3.warning(f"Crude Fiber Too High: {audit_fiber:.2f}% (limit {t_data['max_fiber']}%)")

            aud4.info(f"💡 Total Batch Cost: {total_cost:,.0f} TSH")

            st.markdown("#### Digestible Amino Acids, Available Minerals & Quality Score")
            aa1, aa2, aa3, mn1, mn2, q_metric = st.columns(6)
            aa1.metric("Dig. Lysine", f"{audit_lys:.2f}%")
            aa2.metric("Dig. Methionine", f"{audit_met:.2f}%")
            aa3.metric("Dig. Tryptophan", f"{audit_tryp:.2f}%")
            mn1.metric("Total Calcium", f"{audit_ca:.2f}%")
            mn2.metric("Available Phosphorus", f"{audit_phos:.2f}%")
            q_metric.metric("Calculated PQI Score", f"{audit_pqi:.2f}", f"Baseline Target: {t_data['min_pqi']}")

        else:
            actual_constraints_len = len(A_ub)
            c_diag = list(c) + [100000.0] * actual_constraints_len
            bounds_diag = list(bounds) + [(0.0, 1.0)] * actual_constraints_len

            A_ub_diag = []
            for row_idx, row_vals in enumerate(A_ub):
                slack_row = [0.0] * actual_constraints_len
                slack_row[row_idx] = -1.0
                A_ub_diag.append(list(row_vals) + slack_row)

            A_eq_diag = [list(A_eq[0]) + [0.0] * actual_constraints_len]

            res_diag = linprog(c=c_diag, A_ub=A_ub_diag, b_ub=b_ub, A_eq=A_eq_diag, b_eq=b_eq, bounds=bounds_diag, method="highs")

            # Plain-language cause + one concrete fix, instead of a multi-line technical
            # dump — pick the single biggest problem and say it simply.
            simple_reason = {
                "Protein Deficit (min CP)": "there isn't enough protein in your selected ingredients. Try adding **Soya Meal** or **Fish Meal**.",
                "Energy Deficit (min ME)": "there isn't enough energy in your selected ingredients. Try increasing **Maize** or adding **Vegetable Oil**.",
                "Digestible Lysine Shortage": "the lysine level is too low. Try adding **L-Lysine HCL**.",
                "Digestible Methionine Shortage": "the methionine level is too low. Try adding **DL-Methionine**.",
                "Calcium Deficit": "there isn't enough calcium. Try adding more **Limestone** or **DCP**.",
                "Available Phosphorus Deficit": "there isn't enough available phosphorus. Try adding **DCP** or **Fish Meal**.",
                "Crude Fiber Excess": "the mix has too much fibre. Try reducing **Rice Bran**, **Cotton Seed Cake**, or **Coconut Cake**.",
                "Sorghum Energy Ratio Deficit": "there's too much Sorghum relative to other energy sources. Try adding **Maize Bran** or reducing Sorghum.",
            }

            if res_diag.success:
                slack_results = res_diag.x[num_ingredients:]
                # pick whichever constraint is violated by the largest margin
                worst_label, worst_slack = None, 0
                for label, slack in zip(constraint_labels, slack_results):
                    if slack > worst_slack and label in simple_reason:
                        worst_label, worst_slack = label, slack
                if worst_label:
                    st.error(f"❌ Couldn't build a working formula — {simple_reason[worst_label]}")
                else:
                    st.error("❌ Couldn't build a working formula — the selected ingredients can't meet this stage's targets together. Try adding a wider mix of ingredients.")
            else:
                st.error("❌ Couldn't build a working formula — the selected ingredients are too limited. Try adding more ingredients to the pool.")

    # --- 7. GUIDE SECTION ---
    elif menu == txt["guide"]:
        st.title("📚 Feed Formulation Guide & Legal Framework")
        if lang == "English":
            st.markdown("""
            ### 🧪 Formulation Fundamentals
            Poultry performance relies entirely on balancing **Crude Protein (CP)** for structural tissue growth and **Metabolizable Energy (ME)** for systemic function.

            Amino acid and phosphorus targets in this tool are expressed on a **digestible** basis
            (standardized ileal digestible amino acids, available phosphorus) rather than total
            content — because two ingredients with the same *total* amino acid content can deliver
            very different amounts to the bird depending on fiber, phytate, and chitin content.
            """)
        else:
            st.markdown("""
            ### 🧪 Misingi ya Lishe ya Kuku
            Mavuno na ukuaji bora wa kuku hutegemea uwiano thabiti wa **Crude Protein (CP)** na **Metabolizable Energy (ME)**.

            Malengo ya amino asidi na fosforasi katika chombo hiki yanaonyeshwa kwa msingi wa
            **usagaji halisi** (digestible), sio kiwango cha jumla — kwa sababu malisho mawili
            yenye kiwango sawa cha jumla cha amino asidi yanaweza kutoa kiasi tofauti sana kwa
            kuku kutegemea na nyuzinyuzi (fiber) na vitu vingine visivyosagika kikamilifu.
            """)

        st.subheader("🇹🇿 Tanzania Bureau of Standards (TBS) Official Targets")
        tbs_data = [
            {"Stage": "Broiler Starter", "TBS Crude Protein": "22.0% - 24.0%", "TBS Metabolizable Energy": "3000 kcal/kg"},
            {"Stage": "Broiler Grower", "TBS Crude Protein": "20.0% - 22.0%", "TBS Metabolizable Energy": "3000 kcal/kg"},
            {"Stage": "Broiler Finisher", "TBS Crude Protein": "18.0% - 20.0%", "TBS Metabolizable Energy": "3100 kcal/kg"},
            {"Stage": "Layer Chick Starter", "TBS Crude Protein": "18.5% - 21.0%", "TBS Metabolizable Energy": "2800 kcal/kg"},
            {"Stage": "Layer Grower", "TBS Crude Protein": "15.0% - 17.0%", "TBS Metabolizable Energy": "2700 kcal/kg"},
            {"Stage": "Layer Phase 1 (Laying)", "TBS Crude Protein": "18.0% - 19.5%", "TBS Metabolizable Energy": "2750 kcal/kg"}
        ]
        st.table(pd.DataFrame(tbs_data))

    # --- 8. MARKET SECTION ---
    elif menu == txt["market"]:
        st.title("🛒 Local Feed Ingredient Market Manager")
        st.subheader("📋 Live Pricing Matrix Adjustments")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🌾 Energy & Mineral Sources")
            for name, profile in ING_DATABASE.items():
                if profile["type"] in ["ME", "MIN"]:
                    max_ceil = 12000 if profile["price"] > 8000 else 8000
                    new_price = st.number_input(f"{name} Price (TSH/kg)", min_value=50, max_value=max_ceil, value=int(profile["price"]), step=50, key=f"mkt_prc_{name}")
                    st.session_state["ING_DATABASE"][name]["price"] = new_price

        with c2:
            st.markdown("### 🍗 Protein Sources (CP)")
            for name, profile in ING_DATABASE.items():
                if profile["type"] == "CP":
                    max_ceil = 12000 if profile["price"] > 8000 else 8000
                    new_price = st.number_input(f"{name} Price (TSH/kg)", min_value=100, max_value=max_ceil, value=int(profile["price"]), step=50, key=f"mkt_prc_{name}")
                    st.session_state["ING_DATABASE"][name]["price"] = new_price

    else:
        st.write("Section Content under development.")

# -----------------------------------------------------------------------------
# WORKSPACE LAYER B: TRADER & BUYER PORTAL WORKFLOW
# -----------------------------------------------------------------------------
elif st.session_state["user_role"] == "Trader":
    with st.sidebar:
        st.header("🛒 Buyer Navigation")
        if st.button("🔄 Switch to Farmer Layer", type="secondary"):
            st.session_state["user_role"] = None
            st.rerun()
            
        buyer_lang = st.radio("Language / Lugha:", ["English", "Kiswahili"])
        buyer_menu = st.radio("Go To:", ["🔍 Browse Live Produce", "📋 My Active Orders", "⭐ Farmer Trust Index"])

    if buyer_menu == "🔍 Browse Live Produce":
        st.title("🔍 Live Agricultural Produce Pipeline")
        st.markdown("Filter and acquire healthy local poultry stock from certified farmers nearing harvest timelines.")
        
        b_c1, b_c2 = st.columns(2)
        with b_c1:
            filter_region = st.selectbox("Select Production Region:", ["All Regions", "Dar es Salaam", "Pwani", "Morogoro"])
        with b_c2:
            filter_type = st.selectbox("Produce Type Needed:", ["All Types", "Broiler", "Layer (Culls)"])
            
        st.markdown("### 📋 Available Production Pools (Verified Biosecurity)")
        st.caption("Demo data shown below. Once flocks are listed by farmers, live listings will appear here.")

        mock_pipeline_data = [
            {"Flock Type": "Broiler", "Region": "Dar es Salaam", "District": "Kigamboni", "Volume Available": "450 Birds", "Est. Availability": "In 9 Days", "Asking Price": "8,200 TSH/pc", "Health Check": "100% Fully Vaccinated"},
            {"Flock Type": "Layer (Culls)", "Region": "Pwani", "District": "Chalinze", "Volume Available": "1,200 Birds", "Est. Availability": "Immediate Dressed/Live", "Asking Price": "7,500 TSH/pc", "Health Check": "100% Fully Vaccinated"},
            {"Flock Type": "Broiler", "Region": "Dar es Salaam", "District": "Mbezi", "Volume Available": "800 Birds", "Est. Availability": "In 14 Days", "Asking Price": "8,500 TSH/pc", "Health Check": "100% Fully Vaccinated"}
        ]
        
        df_market = pd.DataFrame(mock_pipeline_data)
        if filter_region != "All Regions":
            df_market = df_market[df_market["Region"] == filter_region]
        if filter_type != "All Types":
            df_market = df_market[df_market["Flock Type"] == filter_type]
            
        st.dataframe(df_market, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🤝 Direct Transaction Connection")
        st.write("Enter the parameters below to trigger a direct transaction dispatch route or request contact access tokens.")
        
        order_col1, order_col2 = st.columns(2)
        with order_col1:
            trader_type = st.selectbox("Your Business Category:", ["Mama Lishe / Food Vendor", "Street Food Caterer", "Domestic Consumer", "Commercial Delivery Service"])
        with order_col2:
            connect_district = st.text_input("Enter District to request Secure Match:", value="Kigamboni")
            
        if st.button("Connect via Secure COD Route"):
            st.success("📩 Request routed to producer queue! The farmer will verify volume parameters and contact you directly for immediate payment-on-delivery arrangement.")

    elif buyer_menu == "📋 My Active Orders":
        st.title("📋 Cash-on-Delivery (COD) Order Tracker")
        st.info("You do not have any pending logistics routes active today. Browse live pools to place requests.")

    elif buyer_menu == "⭐ Farmer Trust Index":
        st.title("⭐ Local Farmer Quality Assurance Scores")
        st.markdown("Historical performance directory tracking production consistency, uniform sizing, and delivery feedback.")
        
        trust_data = [
            {"Farmer ID Hash": "TZ-FARM-902", "Region": "Dar es Salaam", "Completed Batches": 5, "Average FCR Consistency": "High", "Mama Lishe Rating": "⭐⭐⭐⭐⭐ (5.0)"},
            {"Farmer ID Hash": "TZ-FARM-114", "Region": "Pwani", "Completed Batches": 12, "Average FCR Consistency": "Premium", "Mama Lishe Rating": "⭐⭐⭐⭐★ (4.7)"},
            {"Farmer ID Hash": "TZ-FARM-441", "Region": "Morogoro", "Completed Batches": 3, "Average FCR Consistency": "Moderate", "Mama Lishe Rating": "⭐⭐⭐⭐★ (4.2)"}
        ]
        st.table(pd.DataFrame(trust_data))

# --- GLOBAL STABLE FOOTER ---
st.divider()
if st.session_state.get("user_role") == "Farmer":
    st.caption(f"🚀 FeedConvo Pro | {season} Pricing Active")
else:
    st.caption("🚀 FeedConvo Pro Marketplace Layer | Local Decentralized Procurement Engine Active")
