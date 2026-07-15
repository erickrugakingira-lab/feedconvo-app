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

# --- 3. THE DATABASES ---
if "ING_DATABASE" not in st.session_state:
    st.session_state["ING_DATABASE"] = {
        # M.E. Sources
        "Maize": {"prot": 8.0, "en": 3000, "dm_pct": 88.0, "lys": 0.24, "met": 0.18, "tryp": 0.07, "ca": 0.02, "phos": 0.28, "price": 850, "type": "ME", "quality_score": 6},
        "Sorghum": {"prot": 9.0, "en": 3250, "dm_pct": 88.0, "lys": 0.22, "met": 0.16, "tryp": 0.09, "ca": 0.04, "phos": 0.30, "price": 750, "type": "ME", "quality_score": 5},
        "Dehulled Sorghum": {"prot": 9.5, "en": 3300, "dm_pct": 88.0, "lys": 0.23, "met": 0.17, "tryp": 0.09, "ca": 0.03, "phos": 0.29, "price": 850, "type": "ME", "quality_score": 7},
        "Rice Bran": {"prot": 13.5, "en": 3000, "dm_pct": 88.0, "lys": 0.60, "met": 0.25, "tryp": 0.18, "ca": 0.08, "phos": 1.40, "price": 500, "type": "ME", "quality_score": 4},
        "Cassava Meal": {"prot": 2.8, "en": 3000, "dm_pct": 88.0, "lys": 0.10, "met": 0.05, "tryp": 0.03, "ca": 0.12, "phos": 0.11, "price": 600, "type": "ME", "quality_score": 2},
        "Maize Bran": {"prot": 9.4, "en": 2200, "dm_pct": 88.0, "lys": 0.30, "met": 0.14, "tryp": 0.06, "ca": 0.03, "phos": 0.54, "price": 450, "type": "ME", "quality_score": 4},
        "Vegetable Oil": {"prot": 0.0, "en": 8800, "dm_pct": 99.0, "lys": 0.00, "met": 0.00, "tryp": 0.00, "ca": 0.00, "phos": 0.00, "price": 3500, "type": "ME", "quality_score": 0},
        
        # Crude Protein Sources
        "Soya Meal": {"prot": 43.0, "en": 2800, "dm_pct": 88.0, "lys": 2.70, "met": 0.62, "tryp": 0.60, "ca": 0.29, "phos": 0.65, "price": 2300, "type": "CP", "quality_score": 10},
        "Cotton Seed Cake": {"prot": 40.0, "en": 968, "dm_pct": 88.0, "lys": 1.62, "met": 0.55, "tryp": 0.48, "ca": 0.35, "phos": 1.10, "price": 900, "type": "CP", "quality_score": 5},
        "Wheat Pollard": {"prot": 15.0, "en": 2300, "dm_pct": 88.0, "lys": 0.65, "met": 0.22, "tryp": 0.19, "ca": 0.10, "phos": 0.90, "price": 650, "type": "CP", "quality_score": 6},
        "Coconut Cake": {"prot": 21.0, "en": 1650, "dm_pct": 90.0, "lys": 0.68, "met": 0.35, "tryp": 0.22, "ca": 0.20, "phos": 0.60, "price": 800, "type": "CP", "quality_score": 5},
        "BSF Larvae": {"prot": 50.0, "en": 3100, "dm_pct": 88.0, "lys": 3.10, "met": 0.95, "tryp": 0.65, "ca": 0.85, "phos": 0.70, "price": 1500, "type": "CP", "quality_score": 9},
        "Fish Meal": {"prot": 60.0, "en": 2310, "dm_pct": 88.0, "lys": 4.50, "met": 1.80, "tryp": 0.70, "ca": 4.80, "phos": 2.60, "price": 2500, "type": "CP", "quality_score": 10},
        
        # Macro Minerals
        "Limestone": {"prot": 0.0, "en": 0.0, "dm_pct": 99.0, "lys": 0.0, "met": 0.0, "tryp": 0.0, "ca": 38.0, "phos": 0.0, "price": 300, "type": "MIN", "quality_score": 0},
        "DCP": {"prot": 0.0, "en": 0.0, "dm_pct": 99.0, "lys": 0.0, "met": 0.0, "tryp": 0.0, "ca": 21.0, "phos": 18.0, "price": 1200, "type": "MIN", "quality_score": 0},

        # Synthetic Amino Acids & Essentials
        "DL-Methionine": {"prot": 58.0, "en": 0.0, "dm_pct": 99.0, "lys": 0.0, "met": 99.0, "tryp": 0.0, "ca": 0.0, "phos": 0.0, "price": 9500, "type": "CP", "quality_score": 0},
        "L-Lysine HCL": {"prot": 94.0, "en": 0.0, "dm_pct": 99.0, "lys": 78.8, "met": 0.0, "tryp": 0.0, "ca": 0.0, "phos": 0.0, "price": 7500, "type": "CP", "quality_score": 0},
        "Salt": {"prot": 0.0, "en": 0.0, "dm_pct": 99.0, "lys": 0.0, "met": 0.0, "tryp": 0.0, "ca": 0.0, "phos": 0.0, "price": 400, "type": "MIN", "quality_score": 0}
    }

ING_DATABASE = st.session_state["ING_DATABASE"]

STANDARDS = {
    "Broiler": {
        "Starter (Wk 1-2)": {
            "min_cp": 22.5, "max_cp": 24.5, "min_en": 2975, "max_en": 3050,
            "min_lys": 1.32, "max_lys": 1.45, "min_met": 0.55, "max_met": 0.60,
            "min_tryp": 0.21, "max_tryp": 0.28, "min_ca": 0.95, "min_phos": 0.50,
            "bsf_max": 0.05, "bran_max": 0.03, "oil_max": 0.03, "min_pqi": 7.6
        },
        "Grower (Wk 3-4)": {
            "min_cp": 20.5, "max_cp": 22.5, "min_en": 3050, "max_en": 3150,
            "min_lys": 1.18, "max_lys": 1.35, "min_met": 0.51, "max_met": 0.58,
            "min_tryp": 0.19, "max_tryp": 0.25, "min_ca": 0.75, "min_phos": 0.42,
            "bsf_max": 0.10, "bran_max": 0.08, "oil_max": 0.04, "min_pqi": 6.9
        },
        "Finisher (Wk 5+)": {
            "min_cp": 18.0, "max_cp": 20.5, "min_en": 3150, "max_en": 3250,
            "min_lys": 1.08, "max_lys": 1.25, "min_met": 0.48, "max_met": 0.55,
            "min_tryp": 0.17, "max_tryp": 0.22, "min_ca": 0.65, "min_phos": 0.36,
            "bsf_max": 0.15, "bran_max": 0.12, "oil_max": 0.05, "min_pqi": 6.4
        }
    },
    "Layer": {
        "Chick Starter": {
            "min_cp": 18.0, "max_cp": 20.5, "min_en": 2850, "max_en": 3000,
            "min_lys": 0.85, "max_lys": 1.10, "min_met": 0.35, "max_met": 0.50,
            "min_tryp": 0.15, "max_tryp": 0.24, "min_ca": 0.90, "min_phos": 0.40,
            "bsf_max": 0.05, "bran_max": 0.05, "oil_max": 0.02, "min_pqi": 7.4
        },
        "Pullet Grower": {
            "min_cp": 15.0, "max_cp": 17.5, "min_en": 2750, "max_en": 2900,
            "min_lys": 0.65, "max_lys": 0.90, "min_met": 0.30, "max_met": 0.42,
            "min_tryp": 0.12, "max_tryp": 0.20, "min_ca": 0.80, "min_phos": 0.35,
            "bsf_max": 0.10, "bran_max": 0.20, "oil_max": 0.02, "min_pqi": 6.6
        },
        "Layer Phase 1": {
            "min_cp": 18.0, "max_cp": 20.0, "min_en": 2800, "max_en": 2950,
            "min_lys": 0.82, "max_lys": 1.05, "min_met": 0.38, "max_met": 0.52,
            "min_tryp": 0.16, "max_tryp": 0.25, "min_ca": 3.60, "min_phos": 0.45,
            "bsf_max": 0.12, "bran_max": 0.10, "oil_max": 0.03, "min_pqi": 7.0
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
            
            # FCR Calculation Correction: Using Weight Gain instead of total raw weight
            chick_start_weight = 0.04  # Standard Day 1 weight (40 grams)
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
    # INGREDIENT BOUNDARY POLICY CONFIGURATION
        # ==========================================
        # Fallback values defining default maximum inclusion limits if not present in t_data
        INGREDIENT_POLICY = {
            "Limestone": {"min": 0.00, "max": 0.12 if flock_type == "Layer" else 0.06},
            "Sorghum": {"min": 0.00, "max": 0.30},
            "Dehulled Sorghum": {"min": 0.00, "max": 0.50},
            "Fish Meal": {"min": 0.00, "max": 0.15 if "Starter" in stage else 0.12},
            "DL-Methionine": {"min": 0.00, "max": 0.01 if "Starter" in stage else 0.005},
            "L-Lysine HCL": {"min": 0.00, "max": 0.01 if "Starter" in stage else 0.005},
            "Salt": {"min": 0.003, "max": 0.003},
            "Maize": {"min": 0.00, "max": 0.70},
            "DCP": {"min": 0.00, "max": 0.06},
            "BSF Larvae": {"min": 0.00, "max": t_data.get("bsf_max", 0.15)},
            "Maize Bran": {"min": 0.00, "max": t_data.get("bran_max", 0.12)},
            "Vegetable Oil": {"min": 0.00, "max": t_data.get("oil_max", 0.05)}
        }

        premix_pct = 0.005
        toxin_binder_pct = 0.001
        fixed_micro_pct = premix_pct + toxin_binder_pct
        remaining_pct = 1.0 - fixed_micro_pct
        
        ingredient_names = []
        c = [] 
        protein_vals, energy_vals, lys_vals, met_vals, tryp_vals, ca_vals, phos_vals = [], [], [], [], [], [], []
        bounds = []

       # UPDATED BOUNDING LOGIC WITH POLICY MATRIX
            # ==========================================
            if ing in INGREDIENT_POLICY:
               policy = INGREDIENT_POLICY[ing]
               bounds.append((policy["min"], policy["max"]))
            else:
                # Universal fallback safety bounds for unlisted standard ingredients
                bounds.append((0.00, 0.65))

        num_ingredients = len(ingredient_names)
        
        # Build Upper Bound matrix rows dynamically (Relaxed Max caps on Ca/P)
        A_ub = [
            [-p for p in protein_vals], # Min CP
            [p for p in protein_vals],  # Max CP
            [-e for e in energy_vals],  # Min Energy
            [e for e in energy_vals],   # Max Energy
            [-l for l in lys_vals],     # Min Lysine
            [l for l in lys_vals],      # Max Lysine
            [-m for m in met_vals],     # Min Methionine
            [m for m in met_vals],      # Max Methionine
            [-t_val for t_val in tryp_vals], # Min Tryptophan
            [t_val for t_val in tryp_vals],  # Max Tryptophan
            [-ca for ca in ca_vals],    # Min Calcium (No Max cap applied)
            [-ph for ph in phos_vals],  # Min Phosphorus (No Max cap applied)
        ]
        b_ub = [
            -t_data["min_cp"], t_data["max_cp"],
            -t_data["min_en"], t_data["max_en"],
            -t_data["min_lys"], t_data["max_lys"],
            -t_data["min_met"], t_data["max_met"],
            -t_data["min_tryp"], t_data["max_tryp"],
            -t_data["min_ca"],
            -t_data["min_phos"]
        ]

        # Conditional Sorghum Energy Ratio constraints 
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
            A_ub.append(ratio_row)
            b_ub.append(0.00)

        # Space ceiling weight allocation limits
        A_eq = [[1.0] * num_ingredients]
        b_eq = [remaining_pct]

        res = linprog(c=c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")

        if res.success:
            solution = res.x
            recipe_rows = []
            total_cost = 0
            audit_cp = audit_energy = audit_lys = audit_met = audit_tryp = audit_ca = audit_phos = audit_pqi = 0.0

            for i, ing in enumerate(ingredient_names):
                inclusion_pct = solution[i]
                weight_kg = inclusion_pct * total_kg
                ing_price = ING_DATABASE[ing]["price"] * price_multiplier if ing not in ["Limestone", "DCP", "DL-Methionine", "L-Lysine HCL", "Salt"] else ING_DATABASE[ing]["price"]
                cost = weight_kg * ing_price
                
                total_cost += cost
                audit_cp += inclusion_pct * ING_DATABASE[ing]["prot"]
                audit_energy += inclusion_pct * ING_DATABASE[ing]["en"]
                audit_lys += inclusion_pct * ING_DATABASE[ing]["lys"]
                audit_met += inclusion_pct * ING_DATABASE[ing]["met"]
                audit_tryp += inclusion_pct * ING_DATABASE[ing]["tryp"]
                audit_ca += inclusion_pct * ING_DATABASE[ing]["ca"]
                audit_phos += inclusion_pct * ING_DATABASE[ing]["phos"]
                audit_pqi += inclusion_pct * ING_DATABASE[ing].get("quality_score", 0)

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
            m_c3.metric("Ca : P Ratio", f"{ca_phos_ratio:.2f} : 1")

            aud1, aud2, aud3 = st.columns(3)
            if t_data["min_cp"] <= audit_cp <= t_data["max_cp"]:
                aud1.success(f"Crude Protein: {audit_cp:.2f}% (Safe)")
            else:
                aud1.warning(f"Crude Protein Out of Bounds: {audit_cp:.2f}%")

            if t_data["min_en"] <= audit_energy <= t_data["max_en"]:
                aud2.success(f"Energy: {audit_energy:.0f} kcal/kg (Safe)")
            else:
                aud2.warning(f"Energy Out of Bounds: {audit_energy:.0f} kcal")
                
            aud3.info(f"💡 Total Batch Cost: {total_cost:,.0f} TSH")

            st.markdown("#### Amino Acids, Minerals & Post-Formulation Quality Score")
            aa1, aa2, aa3, mn1, mn2, q_metric = st.columns(6)
            aa1.metric("Lysine", f"{audit_lys:.2f}%")
            aa2.metric("Methionine", f"{audit_met:.2f}%")
            aa3.metric("Tryptophan", f"{audit_tryp:.2f}%")
            mn1.metric("Calcium", f"{audit_ca:.2f}%")
            mn2.metric("Phosphorus", f"{audit_phos:.2f}%")
            
            # Post formulation score calculation (Item 1 adjustment output representation)
            q_metric.metric("Calculated PQI Score", f"{audit_pqi:.2f}", f"Baseline Target: {t_data['min_pqi']}")
            
        else:
            st.error("❌ No mathematically feasible solution found.")
            st.markdown("### 🔍 Troubleshooting & Formulation Advice")
            st.info("The system couldn't find a balance that satisfies all metrics simultaneously.")

            # --- DYNAMICALLY ALIGNED ADVANCED DIAGNOSTIC ENGINE ---
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
            
            if res_diag.success:
                slack_results = res_diag.x[num_ingredients:]
                
                # Dynamic diagnostics mapping via positional indices relative to active arrays
                st.warning("⚠️ **Optimization Diagnostics:**")
                if slack_results[0] > 0.001:
                    st.write("- **Protein Deficit:** Add high-protein items like **Soya Meal** or **Fish Meal**.")
                if slack_results[2] > 0.001:
                    st.write("- **Energy Deficit:** Increase the maximum inclusion limit for **Maize** or add **Vegetable Oil**.")
                if slack_results[4] > 0.001:
                    st.write("- **Lysine Shortage:** Verify that **L-Lysine HCL** is activated in the selected ingredient pool.")
                if slack_results[6] > 0.001:
                    st.write("- **Methionine Shortage:** Verify that **DL-Methionine** is checked.")
                if slack_results[10] > 0.001:
                    st.write("- **Calcium Deficit:** Increase your maximum bounds for **Limestone** or **DCP**.")
                if len(slack_results) > 12 and slack_results[12] > 0.001:
                    st.write("- **Sorghum Ratio Deficit:** Mix involves tight energy distribution rules. Enable additional base options like **Maize Bran**.")
            else:
                st.warning("⚠️ The ingredient pool structure is too narrow. Check foundational ingredients to restore baseline functionality.")

    else:
        st.write("Section Content under development.")
# -----------------------------------------------------------------------------
# WORKSPACE LAYER B: TRADER & BUYER VIEWPORT
# -----------------------------------------------------------------------------
elif st.session_state["user_role"] == "Trader":
    st.title("🛒 Trader & Buyer Directory Index")
    selected_district = st.selectbox("Select District:", ['Kinondoni', 'Ilala', 'Temeke', 'Ubungo', 'Kigamboni'])
    
    if supabase:
        try:
            response = supabase.table("farm_records").select("*").eq("is_listed", True).eq("location_district", selected_district).execute()
            if response.data:
                st.dataframe(pd.DataFrame(response.data)[["flock_id", "flock_type", "age_days", "active_birds", "asking_price_tsh"]])
            else:
                st.info("No active flocks currently broadcast within this district profile footprint.")
        except Exception as e:
            st.error(f"Error querying marketplace index data: {e}")

    # --- 7. RESTORED GUIDE SECTION ---
    elif menu == txt["guide"]:
        st.title("📚 Feed Formulation Guide & Legal Framework")
        if lang == "English":
            st.markdown("""
            ### 🧪 Formulation Fundamentals
            Poultry performance relies entirely on balancing **Crude Protein (CP)** for structural tissue growth and **Metabolizable Energy (ME)** for systemic function.
            """)
        else:
            st.markdown("""
            ### 🧪 Misingi ya Lishe ya Kuku
            Mavuno na ukuaji bora wa kuku hutegemea uwiano thabiti wa **Crude Protein (CP)** na **Metabolizable Energy (ME)**.
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

    # --- 8. RESTORED MARKET SECTION ---
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
        
        # Filtering controls tailored for informal/local food providers
        b_c1, b_c2 = st.columns(2)
        with b_c1:
            filter_region = st.selectbox("Select Production Region:", ["All Regions", "Dar es Salaam", "Pwani", "Morogoro"])
        with b_c2:
            filter_type = st.selectbox("Produce Type Needed:", ["All Types", "Broiler", "Layer (Culls)"])
            
        st.markdown("### 📋 Available Production Pools (Verified Biosecurity)")
        
        # Querying pipeline layout using state variables from farm logs
        mock_pipeline_data = [
            {"Flock Type": "Broiler", "Region": "Dar es Salaam", "District": "Kigamboni", "Volume Available": "450 Birds", "Est. Availability": "In 9 Days", "Asking Price": "8,200 TSH/pc", "Health Check": "100% Fully Vaccinated"},
            {"Flock Type": "Layer (Culls)", "Region": "Pwani", "District": "Chalinze", "Volume Available": "1,200 Birds", "Est. Availability": "Immediate Dressed/Live", "Asking Price": "7,500 TSH/pc", "Health Check": "100% Fully Vaccinated"},
            {"Flock Type": "Broiler", "Region": "Dar es Salaam", "District": "Mbezi", "Volume Available": "800 Birds", "Est. Availability": "In 14 Days", "Asking Price": "8,500 TSH/pc", "Health Check": "100% Fully Vaccinated"}
        ]
        
        # Filtering mock dataset context matching selection inputs
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
if st.session_state["user_role"] == "Farmer":
    st.caption(f"🚀 FeedConvo Pro | {season} Pricing Active")
else:
    st.caption("🚀 FeedConvo Pro Marketplace Layer | Local Decentralized Procurement Engine Active")
