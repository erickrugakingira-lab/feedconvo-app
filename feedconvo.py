import streamlit as st
import pandas as pd
import datetime
import os
from scipy.optimize import linprog
import numpy as np
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

# --- 3. THE DATABASES (UPDATED WITH AMINO ACIDS, MINERALS, AND PENALTY SCORES) ---
ING_DATABASE = {
    # M.E. Sources
    "Maize": {"img": "maize_grain.jpg", "prot": 8.0, "en": 3000, "dm_pct": 88.0, "lys": 0.24, "met": 0.18, "tryp": 0.07, "ca": 0.02, "phos": 0.28, "penalty": 1, "price": 850, "type": "ME"},
    "Sorghum": {"img": "sorghum.jpg", "prot": 9.0, "en": 3250, "dm_pct": 88.0, "lys": 0.22, "met": 0.16, "tryp": 0.09, "ca": 0.04, "phos": 0.30, "penalty": 2, "price": 750, "type": "ME"},
    "Rice Bran": {"img": "rice_bran.jpg", "prot": 13.5, "en": 3000, "dm_pct": 88.0, "lys": 0.60, "met": 0.25, "tryp": 0.18, "ca": 0.08, "phos": 1.40, "penalty": 4, "price": 500, "type": "ME"},
    "Cassava Meal": {"img": "cassava_meal.jpg", "prot": 2.8, "en": 3000, "dm_pct": 88.0, "lys": 0.10, "met": 0.05, "tryp": 0.03, "ca": 0.12, "phos": 0.11, "penalty": 3, "price": 600, "type": "ME"},
    "Maize Bran": {"img": "maize_bran.jpg", "prot": 9.4, "en": 2200, "dm_pct": 88.0, "lys": 0.30, "met": 0.14, "tryp": 0.06, "ca": 0.03, "phos": 0.54, "penalty": 1, "price": 450, "type": "ME"},
    "Vegetable Oil": {"img": "vegetable-oil.webp", "prot": 0.0, "en": 8800, "dm_pct": 99.0, "lys": 0.00, "met": 0.00, "tryp": 0.00, "ca": 0.00, "phos": 0.00, "penalty": 2, "price": 3500, "type": "ME"},
    
    # Crude Protein Sources
    "Soya Meal": {"img": "soyameal.jpg", "prot": 43.0, "en": 2800, "dm_pct": 88.0, "lys": 2.70, "met": 0.62, "tryp": 0.60, "ca": 0.29, "phos": 0.65, "penalty": 1, "price": 2300, "type": "CP"},
    "Cotton Seed Cake": {"img": "cottonseed_cake.jpg", "prot": 40.0, "en": 968, "dm_pct": 88.0, "lys": 1.62, "met": 0.55, "tryp": 0.48, "ca": 0.35, "phos": 1.10, "penalty": 4, "price": 900, "type": "CP"},
    "Wheat Pollard": {"img": "wheat_pollard.jpg", "prot": 15.0, "en": 2300, "dm_pct": 88.0, "lys": 0.65, "met": 0.22, "tryp": 0.19, "ca": 0.10, "phos": 0.90, "penalty": 2, "price": 650, "type": "CP"},
    "Coconut Cake": {"img": "coconut_cake.jpg", "prot": 21.0, "en": 1650, "dm_pct": 90.0, "lys": 0.68, "met": 0.35, "tryp": 0.22, "ca": 0.20, "phos": 0.60, "penalty": 3, "price": 800, "type": "CP"},
    "BSF Larvae": {"img": "BSF_larvae.jpg", "prot": 50.0, "en": 3100, "dm_pct": 88.0, "lys": 3.10, "met": 0.95, "tryp": 0.65, "ca": 0.85, "phos": 0.70, "penalty": 2, "price": 1500, "type": "CP"},
    "Fish Meal": {"img": "fishmeal.jpg", "prot": 60.0, "en": 2310, "dm_pct": 88.0, "lys": 4.50, "met": 1.80, "tryp": 0.70, "ca": 4.80, "phos": 2.60, "penalty": 3, "price": 2500, "type": "CP"}
}

# --- BACKEND SAFETY CONSTRAINTS (UPDATED TARGET RANGES FOR AA & MINERALS) ---
STANDARDS = {
    "Broiler": {
        "Starter (Wk 1-2)": {
            "min_cp": 22.0, "max_cp": 24.5, "min_en": 3000, "max_en": 3150, "bsf_max": 0.05, "bran_max": 0.05,
            "min_lys": 1.20, "max_lys": 1.45, "min_met": 0.50, "max_met": 0.65, "min_tryp": 0.20, "max_tryp": 0.30, "min_ca": 0.95, "max_ca": 1.15, "min_phos": 0.45, "max_phos": 0.60
        },
        "Grower (Wk 3-4)": {
            "min_cp": 20.0, "max_cp": 22.0, "min_en": 3000, "max_en": 3200, "bsf_max": 0.10, "bran_max": 0.10,
            "min_lys": 1.05, "max_lys": 1.30, "min_met": 0.45, "max_met": 0.60, "min_tryp": 0.18, "max_tryp": 0.28, "min_ca": 0.85, "max_ca": 1.05, "min_phos": 0.42, "max_phos": 0.55
        },
        "Finisher (Wk 5+)": {
            "min_cp": 18.0, "max_cp": 20.0, "min_en": 3000, "max_en": 3250, "bsf_max": 0.15, "bran_max": 0.15,
            "min_lys": 0.95, "max_lys": 1.20, "min_met": 0.40, "max_met": 0.55, "min_tryp": 0.16, "max_tryp": 0.25, "min_ca": 0.80, "max_ca": 1.00, "min_phos": 0.38, "max_phos": 0.50
        }
    },
    "Layer": {
        "Chick Starter": {
            "min_cp": 18.0, "max_cp": 20.5, "min_en": 2850, "max_en": 3000, "bsf_max": 0.05, "bran_max": 0.05,
            "min_lys": 0.85, "max_lys": 1.10, "min_met": 0.35, "max_met": 0.50, "min_tryp": 0.15, "max_tryp": 0.24, "min_ca": 0.90, "max_ca": 1.10, "min_phos": 0.40, "max_phos": 0.52
        },
        "Pullet Grower": {
            "min_cp": 15.0, "max_cp": 17.5, "min_en": 2750, "max_en": 2900, "bsf_max": 0.10, "bran_max": 0.20,
            "min_lys": 0.65, "max_lys": 0.90, "min_met": 0.30, "max_met": 0.42, "min_tryp": 0.12, "max_tryp": 0.20, "min_ca": 0.80, "max_ca": 1.00, "min_phos": 0.35, "max_phos": 0.48
        },
        "Layer Phase 1": {
            "min_cp": 18.0, "max_cp": 20.0, "min_en": 2800, "max_en": 2950, "bsf_max": 0.12, "bran_max": 0.10,
            "min_lys": 0.82, "max_lys": 1.05, "min_met": 0.38, "max_met": 0.52, "min_tryp": 0.16, "max_tryp": 0.25, "min_ca": 3.60, "max_ca": 4.20, "min_phos": 0.45, "max_phos": 0.58
        }
    }
}

# --- 4. SIDEBAR & SEASONALITY ---
with st.sidebar:
    st.header("🚜 Farm Manager")
    lang = st.radio("Language:", ["English", "Kiswahili"])
    flock_type = st.radio("Select Type:", ["Broiler", "Layer"], key="flock_selector")
    
    st.markdown("### ⚙️ Optimization Strategy")
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

# --- 6. PERFORMANCE FEED SOLVER ---
elif menu == txt["solver"]:
    st.title(f"🚀 {txt['solver']} ({flock_type}) — Mode: {form_mode}")

    stage = st.selectbox("Stage:", list(STANDARDS[flock_type].keys()))
    t_data = STANDARDS[flock_type][stage].copy()

    # --- MODE LOGIC COMPILATION ---
    penalty_weight = 1.0
    if form_mode == "Premium":
        penalty_weight = 0.25
        t_data["min_cp"] += 0.5
        t_data["min_lys"] += 0.05
        t_data["min_met"] += 0.02
    elif form_mode == "Custom Eco":
        penalty_weight = 3.0

    total_kg = st.number_input("Total Feed to Make (kg)", value=100.0)

    st.sidebar.markdown("### 🥣 Select Ingredients")
    available_ingredients = st.sidebar.multiselect(
        "Choose Ingredients for Optimization",
        list(ING_DATABASE.keys()),
        default=["Maize", "Soya Meal", "Fish Meal", "Rice Bran"]
    )

    if len(available_ingredients) < 2:
        st.warning("Please select at least 2 ingredients.")
        st.stop()

    # Fixed micro ingredients inclusion fractions
    oil_pct = 0.015 if flock_type == "Broiler" else 0.01
    premix_pct = 0.005
    toxin_binder_pct = 0.001
    fixed_micro_pct = oil_pct + premix_pct + toxin_binder_pct
    remaining_pct = 1.0 - fixed_micro_pct

    if remaining_pct <= 0:
        st.error("Fixed ingredient percentages exceed 100%")
        st.stop()

    # Build optimization metrics arrays
    ingredient_names = []
    prices_and_penalties = []
    protein_vals = []
    energy_vals = []
    lys_vals = []
    met_vals = []
    tryp_vals = []
    ca_vals = []
    phos_vals = []
    bounds = []

    for ing in available_ingredients:
        if ing in ["Vegetable Oil"]:
            continue

        ingredient_names.append(ing)
        
        raw_price = ING_DATABASE[ing]["price"] * price_multiplier
        penalty_factor = ING_DATABASE[ing]["penalty"] * penalty_weight * 10.0  # Normalized scale factor
        prices_and_penalties.append(raw_price + penalty_factor)
        
        protein_vals.append(ING_DATABASE[ing]["prot"])
        energy_vals.append(ING_DATABASE[ing]["en"])
        lys_vals.append(ING_DATABASE[ing]["lys"])
        met_vals.append(ING_DATABASE[ing]["met"])
        tryp_vals.append(ING_DATABASE[ing]["tryp"])
        ca_vals.append(ING_DATABASE[ing]["ca"])
        phos_vals.append(ING_DATABASE[ing]["phos"])

        if ing == "Fish Meal":
            bounds.append((0.00, 0.10))
        elif ing == "BSF Larvae":
            bounds.append((0.00, t_data["bsf_max"]))
        elif ing == "Maize Bran":
            bounds.append((0.00, t_data["bran_max"]))
        else:
            bounds.append((0.00, 0.80))

    # Optimization Objective
    c = np.array(prices_and_penalties)

    # --- 6a. DYNAMIC PRE-CALCULATION MATRIX STRUCTURE ---
    fixed_cp = 0.0
    fixed_en = oil_pct * ING_DATABASE["Vegetable Oil"]["en"]  # Captures 8800 kcal/kg contribution
    fixed_lys = 0.0
    fixed_met = 0.0
    fixed_tryp = 0.0
    fixed_ca = 0.0
    fixed_phos = 0.0

    # Subtract fixed nutrition pools from targeted profiles
    target_min_cp = t_data["min_cp"] - fixed_cp
    target_max_cp = t_data["max_cp"] - fixed_cp
    target_min_en = t_data["min_en"] - fixed_en
    target_max_en = t_data["max_en"] - fixed_en
    target_min_lys = t_data["min_lys"] - fixed_lys
    target_max_lys = t_data["max_lys"] - fixed_lys
    target_min_met = t_data["min_met"] - fixed_met
    target_max_met = t_data["max_met"] - fixed_met
    target_min_tryp = t_data["min_tryp"] - fixed_tryp
    target_max_tryp = t_data["max_tryp"] - fixed_tryp
    target_min_ca = t_data["min_ca"] - fixed_ca
    target_max_ca = t_data["max_ca"] - fixed_ca
    target_min_phos = t_data["min_phos"] - fixed_phos
    target_max_phos = t_data["max_phos"] - fixed_phos

    A_ub = []
    b_ub = []

    # MIN & MAX CP
    A_ub.append([-p for p in protein_vals])
    b_ub.append(-target_min_cp)
    A_ub.append([p for p in protein_vals])
    b_ub.append(target_max_cp)

    # MIN & MAX ENERGY
    A_ub.append([-e for e in energy_vals])
    b_ub.append(-target_min_en)
    A_ub.append([e for e in energy_vals])
    b_ub.append(target_max_en)

    # MIN & MAX LYSINE
    A_ub.append([-l for l in lys_vals])
    b_ub.append(-target_min_lys)
    A_ub.append([l for l in lys_vals])
    b_ub.append(target_max_lys)

    # MIN & MAX METHIONINE
    A_ub.append([-m for m in met_vals])
    b_ub.append(-target_min_met)
    A_ub.append([m for m in met_vals])
    b_ub.append(target_max_met)

    # MIN & MAX TRYPTOPHAN
    A_ub.append([-t_val for t_val in tryp_vals])
    b_ub.append(-target_min_tryp)
    A_ub.append([t_val for t_val in tryp_vals])
    b_ub.append(target_max_tryp)

    # MIN & MAX CALCIUM
    A_ub.append([-ca for ca in ca_vals])
    b_ub.append(-target_min_ca)
    A_ub.append([ca for ca in ca_vals])
    b_ub.append(target_max_ca)

    # MIN & MAX PHOSPHORUS
    A_ub.append([-ph for ph in phos_vals])
    b_ub.append(-target_min_phos)
    A_ub.append([ph for ph in phos_vals])
    b_ub.append(target_max_phos)

    # Equality Constraint
    A_eq = [[1.0] * len(ingredient_names)]
    b_eq = [remaining_pct]

    # Run Solver
    res = linprog(c=c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")

    if res.success:
        solution = res.x
        recipe_rows = []
        total_cost = 0
        total_penalty = 0
        
        total_cp = 0
        total_energy = 0
        total_lys = 0
        total_met = 0
        total_tryp = 0
        total_ca = 0
        total_phos = 0

        for i, ing in enumerate(ingredient_names):
            inclusion_pct = solution[i]
            weight_kg = inclusion_pct * total_kg
            cost = weight_kg * (ING_DATABASE[ing]["price"] * price_multiplier)
            penalty_score = inclusion_pct * ING_DATABASE[ing]["penalty"]
            
            total_cost += cost
            total_penalty += penalty_score
            
            total_cp += inclusion_pct * ING_DATABASE[ing]["prot"]
            total_energy += inclusion_pct * ING_DATABASE[ing]["en"]
            total_lys += inclusion_pct * ING_DATABASE[ing]["lys"]
            total_met += inclusion_pct * ING_DATABASE[ing]["met"]
            total_tryp += inclusion_pct * ING_DATABASE[ing]["tryp"]
            total_ca += inclusion_pct * ING_DATABASE[ing]["ca"]
            total_phos += inclusion_pct * ING_DATABASE[ing]["phos"]

            recipe_rows.append({
                "Ingredient": ing,
                "Inclusion %": round(inclusion_pct * 100, 2),
                "Amount (kg)": round(weight_kg, 2),
                "Cost (TSH)": round(cost)
            })

        # Append Fixed Additions
        oil_weight = oil_pct * total_kg
        premix_weight = premix_pct * total_kg
        toxin_weight = toxin_binder_pct * total_kg
        oil_cost = oil_weight * ING_DATABASE["Vegetable Oil"]["price"]
        total_cost += oil_cost
        total_penalty += oil_pct * ING_DATABASE["Vegetable Oil"]["penalty"]

        recipe_rows.append({
            "Ingredient": "Vegetable Oil",
            "Inclusion %": round(oil_pct * 100, 2),
            "Amount (kg)": round(oil_weight, 2),
            "Cost (TSH)": round(oil_cost)
        })
        recipe_rows.append({
            "Ingredient": "Premix",
            "Inclusion %": round(premix_pct * 100, 2),
            "Amount (kg)": round(premix_weight, 2),
            "Cost (TSH)": round(premix_weight * 2500)
        })
        recipe_rows.append({
            "Ingredient": "Toxin Binder",
            "Inclusion %": round(toxin_binder_pct * 100, 2),
            "Amount (kg)": round(toxin_weight, 2),
            "Cost (TSH)": round(toxin_weight * 4000)
        })

        recipe_df = pd.DataFrame(recipe_rows)

        st.subheader("🥣 Optimized Feed Formula")
        st.dataframe(recipe_df, use_container_width=True)

        # Final Profiles (As-Fed)
        final_cp = total_cp
        final_energy = total_energy + (oil_pct * ING_DATABASE["Vegetable Oil"]["en"])
        final_lys = total_lys
        final_met = total_met
        final_tryp = total_tryp
        final_ca = total_ca
        final_phos = total_phos

        st.markdown("### 📊 Nutritional Analysis (As-Fed Basis)")
        m_c1, m_c2, m_c3, m_c4 = st.columns(4)
        m_c1.metric("Feed Cost Per Kg", f"{total_cost / total_kg:,.0f} TSH/kg")
        m_c2.metric("Total Formulation Penalty", f"{total_penalty:.2f}")
        m_c3.metric("CP / ME Profiles", f"{final_cp:.1f}% CP | {final_energy:.0f} kcal")
        
        ca_phos_ratio = final_ca / final_phos if final_phos > 0 else 0
        m_c4.metric("Ca : P Ratio", f"{ca_phos_ratio:.2f} : 1")

        # --- 6b. VERIFICATION QUALITY CONTROL ENGINE ---
        st.markdown("### 📊 Nutritional Analysis Audit Summary (Validated on 100% Dry Matter Basis)")
        
        total_dry_mass_kg = 0.0
        total_cp_mass_kg = 0.0
        total_me_pool = 0.0
        total_lys_mass = 0.0
        total_met_mass = 0.0
        total_tryp_mass = 0.0
        total_ca_mass = 0.0
        total_phos_mass = 0.0

        for _, row in recipe_df.iterrows():
            ing_name = row["Ingredient"]
            weight_as_fed = row["Amount (kg)"]
            
            if ing_name in ING_DATABASE:
                db_ref = ING_DATABASE[ing_name]
                dm_factor = db_ref["dm_pct"] / 100.0
                cp_factor = db_ref["prot"] / 100.0
                me_val = db_ref["en"]
                lys_factor = db_ref["lys"] / 100.0
                met_factor = db_ref["met"] / 100.0
                tryp_factor = db_ref["tryp"] / 100.0
                ca_factor = db_ref["ca"] / 100.0
                phos_factor = db_ref["phos"] / 100.0
            elif ing_name in ["Premix", "Toxin Binder"]:
                dm_factor, cp_factor, me_val, lys_factor, met_factor, tryp_factor, ca_factor, phos_factor = 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            else:
                continue

            dry_weight = weight_as_fed * dm_factor
            total_dry_mass_kg += dry_weight
            total_cp_mass_kg += (weight_as_fed * cp_factor)
            total_me_pool += (weight_as_fed * me_val)
            total_lys_mass += (weight_as_fed * lys_factor)
            total_met_mass += (weight_as_fed * met_factor)
            total_tryp_mass += (weight_as_fed * tryp_factor)
            total_ca_mass += (weight_as_fed * ca_factor)
            total_phos_mass += (weight_as_fed * phos_factor)

        if total_dry_mass_kg > 0:
            calculated_cp_dry = (total_cp_mass_kg / total_dry_mass_kg) * 100.0
            calculated_me_dry = total_me_pool / total_dry_mass_kg
            calculated_lys_dry = (total_lys_mass / total_dry_mass_kg) * 100.0
            calculated_met_dry = (total_met_mass / total_dry_mass_kg) * 100.0
            calculated_tryp_dry = (total_tryp_mass / total_dry_mass_kg) * 100.0
            calculated_ca_dry = (total_ca_mass / total_dry_mass_kg) * 100.0
            calculated_phos_dry = (total_phos_mass / total_dry_mass_kg) * 100.0
        else:
            calculated_cp_dry = calculated_me_dry = calculated_lys_dry = calculated_met_dry = calculated_tryp_dry = calculated_ca_dry = calculated_phos_dry = 0.0

        aud1, aud2, aud3 = st.columns(3)
        
        if t_data["min_cp"] <= calculated_cp_dry <= t_data["max_cp"]:
            aud1.success(f"Crude Protein: {calculated_cp_dry:.2f}% (Safe)")
        else:
            aud1.warning(f"Crude Protein: {calculated_cp_dry:.2f}% (Target: {t_data['min_cp']}% - {t_data['max_cp']}%)")

        if t_data["min_en"] <= calculated_me_dry <= t_data["max_en"]:
            aud2.success(f"Energy: {calculated_me_dry:.0f} kcal/kg (Safe)")
        else:
            aud2.warning(f"Energy: {calculated_me_dry:.0f} kcal/kg (Target: {t_data['min_en']} - {t_data['max_en']})")
            
        aud3.info(f"💡 Total Batch Cost: {total_cost:,.0f} TSH")

        # Amino Acid and Mineral Specific Verification Auditing Metrics
        st.markdown("#### Amino Acids & Minerals Audit Details (Dry Basis)")
        aa1, aa2, aa3, mn1, mn2 = st.columns(5)
        
        # Lysine Check
        if t_data["min_lys"] <= calculated_lys_dry <= t_data["max_lys"]:
            aa1.success(f"Lysine: {calculated_lys_dry:.2f}%")
        else:
            aa1.warning(f"Lysine: {calculated_lys_dry:.2f}%")

        # Methionine Check
        if t_data["min_met"] <= calculated_met_dry <= t_data["max_met"]:
            aa2.success(f"Methionine: {calculated_met_dry:.2f}%")
        else:
            aa2.warning(f"Methionine: {calculated_met_dry:.2f}%")

        # Tryptophan Check
        if t_data["min_tryp"] <= calculated_tryp_dry <= t_data["max_tryp"]:
            aa3.success(f"Tryptophan: {calculated_tryp_dry:.2f}%")
        else:
            aa3.warning(f"Tryptophan: {calculated_tryp_dry:.2f}%")

        # Calcium Check
        if t_data["min_ca"] <= calculated_ca_dry <= t_data["max_ca"]:
            mn1.success(f"Calcium: {calculated_ca_dry:.2f}%")
        else:
            mn1.warning(f"Calcium: {calculated_ca_dry:.2f}%")

        # Phosphorus Check
        if t_data["min_phos"] <= calculated_phos_dry <= t_data["max_phos"]:
            mn2.success(f"Phosphorus: {calculated_phos_dry:.2f}%")
        else:
            mn2.warning(f"Phosphorus: {calculated_phos_dry:.2f}%")
    else:
        st.error("❌ No feasible solution found with current ingredients and seasonal targets. Try adding alternative protein or energy sources.")

else:
    st.title("📚 Guide & Market Place")
    st.info("Additional information metrics and guidelines for Tanzanian standards are accessible here.")
