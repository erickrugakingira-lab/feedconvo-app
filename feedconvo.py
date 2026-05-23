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

# --- 3. THE DATABASES (UPDATED WITH DEAS 90: 2023 ANNEX B STANDARDS & DM%) ---
ING_DATABASE = {
    # M.E. Sources
    "Maize": {"img": "maize_grain.jpg", "prot": 8.0, "en": 3000, "dm_pct": 88.0, "price": 850, "type": "ME"},
    "Sorghum": {"img": "sorghum.jpg", "prot": 9.0, "en": 3250, "dm_pct": 88.0, "price": 750, "type": "ME"},
    "Rice Bran": {"img": "rice_bran.jpg", "prot": 13.5, "en": 3000, "dm_pct": 88.0, "price": 500, "type": "ME"},
    "Cassava Meal": {"img": "cassava_meal.jpg", "prot": 2.8, "en": 3000, "dm_pct": 88.0, "price": 600, "type": "ME"},
    "Maize Bran": {"img": "maize_bran.jpg", "prot": 9.4, "en": 2200, "dm_pct": 88.0, "price": 450, "type": "ME"},
    "Vegetable Oil": {"img": "vegetable-oil.webp", "prot": 0.0, "en": 8800, "dm_pct": 99.0, "price": 3500, "type": "ME"},
    
    # Crude Protein Sources
    "Soya Meal": {"img": "soyameal.jpg", "prot": 43.0, "en": 2800, "dm_pct": 88.0, "price": 2300, "type": "CP"},
    "Cotton Seed Cake": {"img": "cottonseed_cake.jpg", "prot": 40.0, "en": 968, "dm_pct": 88.0, "price": 900, "type": "CP"},
    "Wheat Pollard": {"img": "wheat_pollard.jpg", "prot": 15.0, "en": 2300, "dm_pct": 88.0, "price": 650, "type": "CP"},
    "Coconut Cake": {"img": "coconut_cake.jpg", "prot": 21.0, "en": 1650, "dm_pct": 90.0, "price": 800, "type": "CP"},
    "BSF Larvae": {"img": "BSF_larvae.jpg", "prot": 50.0, "en": 3100, "dm_pct": 88.0, "price": 1500, "type": "CP"},
    "Fish Meal": {"img": "fishmeal.jpg", "prot": 60.0, "en": 2310, "dm_pct": 88.0, "price": 2500, "type": "CP"}
}

# --- BACKEND SAFETY CONSTRAINTS (CP & ME MIN/MAX BRACKETS) ---
STANDARDS = {
    "Broiler": {
        "Starter (Wk 1-2)": {"min_cp": 22.0, "max_cp": 24.5, "min_en": 3000, "max_en": 3150, "bsf_max": 0.05, "bran_max": 0.05},
        "Grower (Wk 3-4)": {"min_cp": 20.0, "max_cp": 22.0, "min_en": 3000, "max_en": 3200, "bsf_max": 0.10, "bran_max": 0.10},
        "Finisher (Wk 5+)": {"min_cp": 18.0, "max_cp": 20.0, "min_en": 3000, "max_en": 3250, "bsf_max": 0.15, "bran_max": 0.15}
    },
    "Layer": {
        "Chick Starter": {"min_cp": 18.0, "max_cp": 20.5, "min_en": 2850, "max_en": 3000, "bsf_max": 0.05, "bran_max": 0.05},
        "Pullet Grower": {"min_cp": 15.0, "max_cp": 17.5, "min_en": 2750, "max_en": 2900, "bsf_max": 0.10, "bran_max": 0.20},
        "Layer Phase 1": {"min_cp": 18.0, "max_cp": 20.0, "min_en": 2800, "max_en": 2950, "bsf_max": 0.12, "bran_max": 0.10}
    }
}

# --- 4. SIDEBAR & SEASONALITY ---
with st.sidebar:
    st.header("🚜 Farm Manager")
    lang = st.radio("Language:", ["English", "Kiswahili"])
    flock_type = st.radio("Select Type:", ["Broiler", "Layer"], key="flock_selector")
    
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

# --- 6. PERFORMANCE FEED SOLVER (UPDATED PROFESSIONAL VERSION) ---
elif menu == txt["solver"]:

    from scipy.optimize import linprog
    import numpy as np

    st.title(f"🚀 {txt['solver']} ({flock_type})")

    stage = st.selectbox("Stage:", list(STANDARDS[flock_type].keys()))
    t_data = STANDARDS[flock_type][stage]

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

    # -----------------------------------------
    # FIXED MICRO INGREDIENTS
    # -----------------------------------------

    oil_pct = 0.015 if flock_type == "Broiler" else 0.01
    premix_pct = 0.005
    toxin_binder_pct = 0.001

    fixed_micro_pct = oil_pct + premix_pct + toxin_binder_pct

    remaining_pct = 1.0 - fixed_micro_pct

    if remaining_pct <= 0:
        st.error("Fixed ingredient percentages exceed 100%")
        st.stop()

    # -----------------------------------------
    # BUILD OPTIMIZATION MATRICES
    # -----------------------------------------

    ingredient_names = []
    prices = []
    protein_vals = []
    energy_vals = []

    bounds = []

    for ing in available_ingredients:

        if ing in ["Vegetable Oil"]:
            continue

        ingredient_names.append(ing)

        prices.append(
            ING_DATABASE[ing]["price"] * price_multiplier
        )

        protein_vals.append(
            ING_DATABASE[ing]["prot"]
        )

        energy_vals.append(
            ING_DATABASE[ing]["en"]
        )

        # Ingredient inclusion limits
        if ing == "Fish Meal":
            bounds.append((0.00, 0.10))

        elif ing == "BSF Larvae":
            bounds.append((0.00, t_data["bsf_max"]))

        elif ing == "Maize Bran":
            bounds.append((0.00, t_data["bran_max"]))

        elif ing == "Vegetable Oil":
            bounds.append((0.00, oil_pct))

        else:
            bounds.append((0.00, 0.80))

    # -----------------------------------------
    # OBJECTIVE FUNCTION
    # -----------------------------------------

    c = np.array(prices)

    # -----------------------------------------
    # CONSTRAINTS
    # -----------------------------------------

    A_ub = []
    b_ub = []

    # MIN CP
    A_ub.append([-p for p in protein_vals])
    b_ub.append(-(t_data["min_cp"] * remaining_pct))

    # MAX CP
    A_ub.append([p for p in protein_vals])
    b_ub.append(t_data["max_cp"] * remaining_pct)

    # MIN ENERGY
    A_ub.append([-e for e in energy_vals])
    b_ub.append(-(t_data["min_en"] * remaining_pct))

    # MAX ENERGY
    A_ub.append([e for e in energy_vals])
    b_ub.append(t_data["max_en"] * remaining_pct)

    # Equality Constraint
    A_eq = [[1.0] * len(ingredient_names)]
    b_eq = [remaining_pct]

    # -----------------------------------------
    # SOLVE
    # -----------------------------------------

    res = linprog(
        c=c,
        A_ub=A_ub,
        b_ub=b_ub,
        A_eq=A_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs"
    )

    # -----------------------------------------
    # RESULTS
    # -----------------------------------------

    if res.success:

        solution = res.x

        recipe_rows = []

        total_cost = 0
        total_cp = 0
        total_energy = 0

        for i, ing in enumerate(ingredient_names):

            inclusion_pct = solution[i]

            weight_kg = inclusion_pct * total_kg

            cost = weight_kg * (
                ING_DATABASE[ing]["price"] * price_multiplier
            )

            cp_contrib = inclusion_pct * ING_DATABASE[ing]["prot"]

            energy_contrib = inclusion_pct * ING_DATABASE[ing]["en"]

            total_cost += cost
            total_cp += cp_contrib
            total_energy += energy_contrib

            recipe_rows.append({
                "Ingredient": ing,
                "Inclusion %": round(inclusion_pct * 100, 2),
                "Amount (kg)": round(weight_kg, 2),
                "Cost (TSH)": round(cost)
            })

        # Add fixed ingredients
        oil_weight = oil_pct * total_kg
        premix_weight = premix_pct * total_kg
        toxin_weight = toxin_binder_pct * total_kg

        oil_cost = oil_weight * ING_DATABASE["Vegetable Oil"]["price"]

        total_cost += oil_cost

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

        # -----------------------------------------
        # FINAL NUTRITIONAL ANALYSIS
        # -----------------------------------------

        final_cp = total_cp

        final_energy = total_energy + (
            oil_pct * ING_DATABASE["Vegetable Oil"]["en"]
        )

        st.markdown("### 📊 Nutritional Analysis")

        c1, c2, c3 = st.columns(3)

        if t_data["min_cp"] <= final_cp <= t_data["max_cp"]:
            c1.success(f"CP: {final_cp:.2f}%")
        else:
            c1.error(f"CP: {final_cp:.2f}%")

        if t_data["min_en"] <= final_energy <= t_data["max_en"]:
            c2.success(f"ME: {final_energy:.0f} kcal/kg")
        else:
            c2.error(f"ME: {final_energy:.0f} kcal/kg")

        c3.info(f"Cost: {total_cost:,.0f} TSH")

        # -----------------------------------------
        # COST PER KG
        # -----------------------------------------

        cost_per_kg = total_cost / total_kg

        st.metric(
            "Feed Cost Per Kg",
            f"{cost_per_kg:,.0f} TSH/kg"
        )

    else:

        st.error("❌ No feasible solution found.")

        st.info("""
Possible causes:
- Protein target too high
- Energy target too high
- Ingredient selection too limited
- Inclusion limits too restrictive
- Ingredient nutrient values unrealistic
""")
        
        # --- VERIFICATION QUALITY CONTROL ENGINE ---
        # Back-calculating actual nutrient delivery fractions on standard 100% Dry Matter basis
        total_dry_mass_kg = (
            (w_me_grain * dm_me) + (w_cp_meal * dm_cp) + 
            (w_bsf * dm_bsf) + (w_bran * dm_bran) + (w_oil * 0.99)
        )
        
        calculated_cp_dry = (
            (w_me_grain * (ING_DATABASE[me_choice]["prot"] / 100.0)) +
            (w_cp_meal * (ING_DATABASE[cp_choice]["prot"] / 100.0)) +
            (w_bsf * (ING_DATABASE["BSF Larvae"]["prot"] / 100.0)) +
            (w_bran * (ING_DATABASE["Maize Bran"]["prot"] / 100.0))
        ) / total_dry_mass_kg * 100.0

        calculated_me_dry = (
            (w_me_grain * ING_DATABASE[me_choice]["en"]) +
            (w_cp_meal * ING_DATABASE[cp_choice]["en"]) +
            (w_bsf * ING_DATABASE["BSF Larvae"]["en"]) +
            (w_bran * ING_DATABASE["Maize Bran"]["en"]) +
            (w_oil * ING_DATABASE["Vegetable Oil"]["en"])
        ) / total_dry_mass_kg

        # Standardizing output representation display metrics
        st.markdown("### 📊 Nutritional Analysis Audit Summary (Validated on 100% Dry Matter Basis)")
        c1, c2, c3 = st.columns(3)
        
        if t_data["min_cp"] <= calculated_cp_dry <= t_data["max_cp"]:
            c1.success(f"Crude Protein: {calculated_cp_dry:.2f}% (Safe Range)")
        else:
            c1.warning(f"Crude Protein: {calculated_cp_dry:.2f}% (Target: {t_data['min_cp']}% - {t_data['max_cp']}%)")

        if t_data["min_en"] <= calculated_me_dry <= t_data["max_en"]:
            c2.success(f"Metabolizable Energy: {calculated_me_dry:.0f} kcal/kg (Safe Range)")
        else:
            c2.warning(f"Energy: {calculated_me_dry:.0f} kcal/kg (Target: {t_data['min_en']} - {t_data['max_en']})")
            
        st.info(f"💡 Total Batch Cost: {recipe_df['Cost (TSH)'].sum():,.0f} TSH")
        else:
        st.error(f"❌ Feasibility Constraint Block: Using exclusively **{me_choice}** and **{cp_choice}** with your current dry fixed additions, it is mathematically impossible to cross both minimum nutrition metrics ({t_data['min_cp']}% CP & {t_data['min_en']} kcal/kg ME) safely without violating the max safety ceilings.")
        st.info("💡 **Solution:** Try switching your primary grain selector to an alternative energy source like **Sorghum**, or add a higher performance matrix choice in your protein sidebar selection field.")

# --- 7. GUIDE & MARKET ---
elif menu == txt["guide"]:
    st.title(txt["guide"])
    sel = st.selectbox("Select Ingredient Reference Profile:", list(ING_DATABASE.keys()))
    inf = ING_DATABASE[sel]
    st.markdown(f"### Official DEAS 90: 2023 Specifications for **{sel}**")
    st.write(f"• **Dry Matter (DM):** {inf['dm_pct']}%")
    st.write(f"• **Crude Protein (CP):** {inf['prot']}%")
    st.write(f"• **Energy (ME):** {inf['en']} kcal/kg")

elif menu == txt["market"]:
    st.title(txt["market"])
    for name, info in ING_DATABASE.items():
        curr_p = round(info['price'] * price_multiplier)
        c1, c2, c3 = st.columns([2, 1, 1])
        c1.write(f"**{name}** ({info['type']} Vector)")
        c2.write(f"{curr_p} TSH/kg")
        c3.link_button("Order", f"https://wa.me/255777744657?text=I%20want%20to%20order%20{name}")

st.divider()
st.caption(f"🚀 FeedConvo Pro | {season} Pricing System Configured with East African Dry Matter Controls.")
