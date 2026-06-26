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

# --- 3. THE DATABASES ---
if "ING_DATABASE" not in st.session_state:
    st.session_state["ING_DATABASE"] = {
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
        "Fish Meal": {"img": "fishmeal.jpg", "prot": 60.0, "en": 2310, "dm_pct": 88.0, "lys": 4.50, "met": 1.80, "tryp": 0.70, "ca": 4.80, "phos": 2.60, "penalty": 3, "price": 2500, "type": "CP"},
        
        # Macro Mineral Replacements
        "Limestone": {"img": "limestone.jpg", "prot": 0.0, "en": 0.0, "dm_pct": 99.0, "lys": 0.0, "met": 0.0, "tryp": 0.0, "ca": 38.0, "phos": 0.0, "penalty": 1, "price": 300, "type": "MIN"},
        "DCP": {"img": "dcp.jpg", "prot": 0.0, "en": 0.0, "dm_pct": 99.0, "lys": 0.0, "met": 0.0, "tryp": 0.0, "ca": 21.0, "phos": 18.0, "penalty": 1, "price": 1200, "type": "MIN"},

        # Synthetic Amino Acids & Essentials
        "DL-Methionine": {"img": "synthetic_aa.jpg", "prot": 58.0, "en": 0.0, "dm_pct": 99.0, "lys": 0.0, "met": 99.0, "tryp": 0.0, "ca": 0.0, "phos": 0.0, "penalty": 0, "price": 9500, "type": "CP"},
        "L-Lysine HCL": {"img": "synthetic_aa.jpg", "prot": 94.0, "en": 0.0, "dm_pct": 99.0, "lys": 78.8, "met": 0.0, "tryp": 0.0, "ca": 0.0, "phos": 0.0, "penalty": 0, "price": 7500, "type": "CP"},
        "Salt": {"img": "salt.jpg", "prot": 0.0, "en": 0.0, "dm_pct": 99.0, "lys": 0.0, "met": 0.0, "tryp": 0.0, "ca": 0.0, "phos": 0.0, "penalty": 0, "price": 400, "type": "MIN"}
    }

ING_DATABASE = st.session_state["ING_DATABASE"]

STANDARDS = {
    "Broiler": {
        "Starter (Wk 1-2)": {
            "min_cp": 22.5, "max_cp": 24.5,
            "min_en": 2975, "max_en": 3050,
            "min_lys": 1.32, "max_lys": 1.45,
            "min_met": 0.55, "max_met": 0.60,
            "min_tryp": 0.21, "max_tryp": 0.28,
            "min_ca": 0.95, "max_ca": 1.10,
            "min_phos": 0.50, "max_phos": 0.60,
            "bsf_max": 0.05, "bran_max": 0.03, "oil_max": 0.03
        },
        "Grower (Wk 3-4)": {
            "min_cp": 20.5, "max_cp": 22.5,
            "min_en": 3050, "max_en": 3150,
            "min_lys": 1.18, "max_lys": 1.35,
            "min_met": 0.51, "max_met": 0.58,
            "min_tryp": 0.19, "max_tryp": 0.25,
            "min_ca": 0.75, "max_ca": 0.95,
            "min_phos": 0.42, "max_phos": 0.55,
            "bsf_max": 0.10, "bran_max": 0.08, "oil_max": 0.04
        },
        "Finisher (Wk 5+)": {
            "min_cp": 18.0, "max_cp": 20.5,
            "min_en": 3150, "max_en": 3250,
            "min_lys": 1.08, "max_lys": 1.25,
            "min_met": 0.48, "max_met": 0.55,
            "min_tryp": 0.17, "max_tryp": 0.22,
            "min_ca": 0.65, "max_ca": 0.85,
            "min_phos": 0.36, "max_phos": 0.50,
            "bsf_max": 0.15, "bran_max": 0.12, "oil_max": 0.05
        }
    },
    "Layer": {
        "Chick Starter": {
            "min_cp": 18.0, "max_cp": 20.5,
            "min_en": 2850, "max_en": 3000,
            "min_lys": 0.85, "max_lys": 1.10,
            "min_met": 0.35, "max_met": 0.50,
            "min_tryp": 0.15, "max_tryp": 0.24,
            "min_ca": 0.90, "max_ca": 1.10,
            "min_phos": 0.40, "max_phos": 0.52,
            "bsf_max": 0.05, "bran_max": 0.05, "oil_max": 0.02
        },
        "Pullet Grower": {
            "min_cp": 15.0, "max_cp": 17.5,
            "min_en": 2750, "max_en": 2900,
            "min_lys": 0.65, "max_lys": 0.90,
            "min_met": 0.30, "max_met": 0.42,
            "min_tryp": 0.12, "max_tryp": 0.20,
            "min_ca": 0.80, "max_ca": 1.00,
            "min_phos": 0.35, "max_phos": 0.48,
            "bsf_max": 0.10, "bran_max": 0.20, "oil_max": 0.02
        },
        "Layer Phase 1": {
            "min_cp": 18.0, "max_cp": 20.0,
            "min_en": 2800, "max_en": 2950,
            "min_lys": 0.82, "max_lys": 1.05,
            "min_met": 0.38, "max_met": 0.52,
            "min_tryp": 0.16, "max_tryp": 0.25,
            "min_ca": 3.60, "max_ca": 4.20,
            "min_phos": 0.45, "max_phos": 0.58,
            "bsf_max": 0.12, "bran_max": 0.10, "oil_max": 0.03
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

# --- 6. LEAST-COST RATION FEED SOLVER ---
elif menu == txt["solver"]:
    st.title(f"🚀 {txt['solver']} ({flock_type}) — Least Cost Optimization")

    stage = st.selectbox("Stage:", list(STANDARDS[flock_type].keys()))
    t_data = STANDARDS[flock_type][stage].copy()

    # Apply structural modifications matching formulation profile changes
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

    premix_pct = 0.005
    toxin_binder_pct = 0.001
    fixed_micro_pct = premix_pct + toxin_binder_pct
    remaining_pct = 1.0 - fixed_micro_pct

    ingredient_names = []
    c = []  # Strictly raw financial costs
    protein_vals = []
    energy_vals = []
    lys_vals = []
    met_vals = []
    tryp_vals = []
    ca_vals = []
    phos_vals = []
    bounds = []

    for ing in available_ingredients:
        ingredient_names.append(ing)
        raw_price = ING_DATABASE[ing]["price"] * price_multiplier if ing not in ["Limestone", "DCP", "DL-Methionine", "L-Lysine HCL", "Salt"] else ING_DATABASE[ing]["price"]
        c.append(raw_price)
        
        protein_vals.append(ING_DATABASE[ing]["prot"])
        energy_vals.append(ING_DATABASE[ing]["en"])
        lys_vals.append(ING_DATABASE[ing]["lys"])
        met_vals.append(ING_DATABASE[ing]["met"])
        tryp_vals.append(ING_DATABASE[ing]["tryp"])
        ca_vals.append(ING_DATABASE[ing]["ca"])
        phos_vals.append(ING_DATABASE[ing]["phos"])

        if ing == "Fish Meal":
            bounds.append((0.00, 0.12))
        elif ing in ["DL-Methionine", "L-Lysine HCL"]:
            bounds.append((0.00, 0.005))
        elif ing == "Salt":
            bounds.append((0.003, 0.003))
        elif ing == "BSF Larvae":
            bounds.append((0.00, t_data["bsf_max"]))
        elif ing == "Maize Bran":
            bounds.append((0.00, t_data["bran_max"]))
        elif ing == "Vegetable Oil":
            bounds.append((0.00, t_data["oil_max"]))
        elif ing == "Maize":
            bounds.append((0.00, 0.70))
        elif ing in ["Limestone", "DCP"]:
            bounds.append((0.00, 0.06))
        else:
            bounds.append((0.00, 0.65))

    num_ingredients = len(ingredient_names)
    
    # Pure lower-bound inequalities (converted to <= form for scipy by multiplying by -1)
    A_ub = [
        [-p for p in protein_vals],
        [p for p in protein_vals],
        [-e for e in energy_vals],
        [e for e in energy_vals],
        [-l for l in lys_vals],
        [l for l in lys_vals],
        [-m for m in met_vals],
        [m for m in met_vals],
        [-t_val for t_val in tryp_vals],
        [t_val for t_val in tryp_vals],
        [-ca for ca in ca_vals],
        [ca for ca in ca_vals],
        [-ph for ph in phos_vals],
        [ph for ph in phos_vals]
    ]
    b_ub = [
        -t_data["min_cp"], t_data["max_cp"],
        -t_data["min_en"], t_data["max_en"],
        -t_data["min_lys"], t_data["max_lys"],
        -t_data["min_met"], t_data["max_met"],
        -t_data["min_tryp"], t_data["max_tryp"],
        -t_data["min_ca"], t_data["max_ca"],
        -t_data["min_phos"], t_data["max_phos"]
    ]

    # Batch weight equality lock matching space limits
    A_eq = [[1.0] * num_ingredients]
    b_eq = [remaining_pct]

    res = linprog(c=c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")

    if res.success:
        solution = res.x
        recipe_rows = []
        total_cost = 0
        
        audit_cp = audit_energy = audit_lys = audit_met = audit_tryp = audit_ca = audit_phos = 0.0

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
            aud1.success(f"Crude Protein: {audit_cp:.2f}% (Safe Range)")
        else:
            aud1.warning(f"Crude Protein Out of Bounds: {audit_cp:.2f}%")

        if t_data["min_en"] <= audit_energy <= t_data["max_en"]:
            aud2.success(f"Energy: {audit_energy:.0f} kcal/kg (Safe Range)")
        else:
            aud2.warning(f"Energy Out of Bounds: {audit_energy:.0f} kcal")
            
        aud3.info(f"💡 Total Batch Cost: {total_cost:,.0f} TSH")

        st.markdown("#### Amino Acids & Minerals Details")
        aa1, aa2, aa3, mn1, mn2 = st.columns(5)
        aa1.metric("Lysine", f"{audit_lys:.2f}%")
        aa2.metric("Methionine", f"{audit_met:.2f}%")
        aa3.metric("Tryptophan", f"{audit_tryp:.2f}%")
        mn1.metric("Calcium", f"{audit_ca:.2f}%")
        mn2.metric("Phosphorus", f"{audit_phos:.2f}%")
        
    else:
        st.error("❌ No mathematically feasible solution found.")
        st.markdown("### 🔍 Advanced Infeasibility Diagnostic Report")
        st.warning("The selected ingredients cannot satisfy your target constraints. Evaluating limiting factors below:")

        traits_checklist = [
            ("Crude Protein", protein_vals, t_data["min_cp"], "%"),
            ("Metabolizable Energy", energy_vals, t_data["min_en"], " kcal/kg"),
            ("Lysine", lys_vals, t_data["min_lys"], "%"),
            ("Methionine", met_vals, t_data["min_met"], "%"),
            ("Calcium", ca_vals, t_data["min_ca"], "%"),
            ("Phosphorus", phos_vals, t_data["min_phos"], "%")
        ]

        for label, values, required_min, unit in traits_checklist:
            max_possible_yield = sum(bounds[idx][1] * values[idx] for idx in range(num_ingredients))
            if max_possible_yield < required_min:
                st.error(f"🚨 **{label} Deficit:** Your chosen ingredient pool provides a maximum potential of only **{max_possible_yield:.2f}{unit}**, failing to meet the mandatory **{required_min:.2f}{unit}** minimum benchmark.")
            else:
                st.write(f"✅ {label}: Ingredient capacities can theoretically cover this floor.")

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

st.divider()
st.caption(f"🚀 FeedConvo Pro | {season} Pricing Active")
