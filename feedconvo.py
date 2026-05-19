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

# --- 6. PERFORMANCE FEED SOLVER (LINEAR PROGRAMMING & DRY MATTER CONVERGENCE) ---
elif menu == txt["solver"]:
    st.title(f"🚀 {txt['solver']} ({flock_type})")
    stage = st.selectbox("Stage:", list(STANDARDS[flock_type].keys()))
    t_data = STANDARDS[flock_type][stage]
    total_kg = st.number_input("Total Feed to Make (kg)", value=100.0)

    st.sidebar.markdown("### 🥣 Select Available Base Ingredients")
    
    # Filter groups from database dynamically so the user can control what goes to the solver
    me_options = [k for k, v in ING_DATABASE.items() if v["type"] == "ME" and k not in ["Vegetable Oil", "Maize Bran"]]
    cp_options = [k for k, v in ING_DATABASE.items() if v["type"] == "CP" and k != "BSF Larvae"]

    me_choice = st.sidebar.selectbox("Primary ME Grain Source:", me_options)
    cp_choice = st.sidebar.selectbox("Primary CP Meal Source:", cp_options)

    # FIXED USER OVERRIDES (Inclusions & Checkboxes)
    oil_pct = 0.02 if flock_type == "Broiler" else 0.01 
    premix_min_pct = 0.05 
    toxin_binder_pct = 0.02 
    use_bsf = st.checkbox("Include BSF Larvae (Sustainable CP Boost)", value=True)
    use_bran = st.checkbox("Include Maize Bran (Cost Saver Fiber)", value=True)

    bsf_pct = t_data["bsf_max"] if use_bsf else 0.0
    bran_pct = t_data["bran_max"] if use_bran else 0.0
    
    # FIXED SUB-POOL CALCULATIONS
    w_oil = total_kg * oil_pct
    w_bsf = total_kg * bsf_pct
    w_bran = total_kg * bran_pct
    w_others = total_kg * (premix_min_pct + toxin_binder_pct)
    
    fixed_space = oil_pct + premix_min_pct + toxin_binder_pct + bsf_pct + bran_pct
    rem_space = 1.0 - fixed_space

    # --- LINEAR PROGRAMMING SOLVER WITH DRY MATTER ENGINE ---
    from scipy.optimize import linprog

    # Macro pool ingredients available for structural solving calculation
    solver_ingredients = [me_choice, cp_choice]
    
    # 1. Objective Function Vector (Minimize As-Fed seasonal pricing weight costs)
    c_vector = [ING_DATABASE[ing]["price"] * price_multiplier for ing in solver_ingredients]

    # 2. Extracting Dry Matter Ratios
    dm_me = ING_DATABASE[me_choice]["dm_pct"] / 100.0
    dm_cp = ING_DATABASE[cp_choice]["dm_pct"] / 100.0
    dm_bsf = ING_DATABASE["BSF Larvae"]["dm_pct"] / 100.0
    dm_bran = ING_DATABASE["Maize Bran"]["dm_pct"] / 100.0

    # Calculate nutrient yields provided by the fixed ingredient blocks on a 100% Dry Matter basis
    p_fixed_dry = 0.0
    en_fixed_dry = 0.0

    if use_bsf:
        p_fixed_dry += bsf_pct * (ING_DATABASE["BSF Larvae"]["prot"] / dm_bsf)
        en_fixed_dry += bsf_pct * (ING_DATABASE["BSF Larvae"]["en"] / dm_bsf)
    if use_bran:
        p_fixed_dry += bran_pct * (ING_DATABASE["Maize Bran"]["prot"] / dm_bran)
        en_fixed_dry += bran_pct * (ING_DATABASE["Maize Bran"]["en"] / dm_bran)
        
    # Fat/Oil matrix contribution (virtually moisture free)
    en_fixed_dry += oil_pct * (ING_DATABASE["Vegetable Oil"]["en"] / 0.99)

    # 3. Formulating Dry Nutrient Constraints for the Solver Pool (A_ub * x <= b_ub)
    # Scipy looks for <= equations, so minimums are flipped using negative multiplication
    A_ub = []
    b_ub = []

    # Get Dry Protein values for optimization variables
    prot_me_dry = ING_DATABASE[me_choice]["prot"] / dm_me
    prot_cp_dry = ING_DATABASE[cp_choice]["prot"] / dm_cp
    
    # Get Dry Energy values for optimization variables
    en_me_dry = ING_DATABASE[me_choice]["en"] / dm_me
    en_cp_dry = ING_DATABASE[cp_choice]["en"] / dm_cp

    # Constraint Line A: Minimum Crude Protein Threshold (Dry Basis)
    A_ub.append([-prot_me_dry, -prot_cp_dry])
    b_ub.append(-(t_data["min_cp"] - p_fixed_dry))

    # Constraint Line B: Maximum Crude Protein Threshold (Dry Basis Safety Ceiling)
    A_ub.append([prot_me_dry, prot_cp_dry])
    b_ub.append(t_data["max_cp"] - p_fixed_dry)

    # Constraint Line C: Minimum Metabolizable Energy Threshold (Dry Basis)
    A_ub.append([-en_me_dry, -en_cp_dry])
    b_ub.append(-(t_data["min_en"] - en_fixed_dry))

    # Constraint Line D: Maximum Metabolizable Energy Threshold (Dry Basis Safety Ceiling)
    A_ub.append([en_me_dry, en_cp_dry])
    b_ub.append(t_data["max_en"] - en_fixed_dry)

    # 4. Equality Constraint (Total allocated macro solver variables must match exact target rem_space)
    A_eq = [[1.0, 1.0]]
    b_eq = [rem_space]

    # Boundaries: Inclusions must remain between 0% and 100% of remaining space
    x_bounds = [(0.0, rem_space), (0.0, rem_space)]

    # Compute Optimization Function Matrix
    res = linprog(c_vector, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=x_bounds, method="highs")

    if res.success:
        # Dynamic variable array unraveling back out to Physical As-Fed weight profiles
        w_me_grain = res.x[0] * total_kg
        w_cp_meal = res.x[1] * total_kg

        st.subheader("🥣 Optimized Mixing Table (Recipe output scaled As-Fed)")
        recipe_df = pd.DataFrame({
            "Ingredient": [f"{me_choice} (Base)", f"{cp_choice} (Protein Source)", "BSF Larvae", "Maize Bran", "Vegetable Oil", "Premix & Toxin Binder"],
            "Amount (kg)": [round(w_me_grain, 1), round(w_cp_meal, 1), round(w_bsf, 1), round(w_bran, 1), round(w_oil, 1), round(w_others, 1)],
            "Cost (TSH)": [
                round(w_me_grain * ING_DATABASE[me_choice]["price"] * price_multiplier),
                round(w_cp_meal * ING_DATABASE[cp_choice]["price"] * price_multiplier),
                round(w_bsf * ING_DATABASE["BSF Larvae"]["price"]),
                round(w_bran * ING_DATABASE["Maize Bran"]["price"] * price_multiplier),
                round(w_oil * ING_DATABASE["Vegetable Oil"]["price"]),
                round(w_others * 2500)
            ]
        })
        st.table(recipe_df)
        
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
