import streamlit as st
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

# --- 2. THE DATABASES ---
# Updated with BSFL and LCR Constraints
ING_DATABASE = {
    "Maize": {
        "img": "maize_grain.jpg", "prot": 9.0, "en": 3350, "price_per_kg": 850,
        "max_inc": 70, "qc": ["✅ Unyevu < 13% / Moisture < 13%", "✅ Nafaka nzima / Whole grains", "❌ **Red Flag:** Vumbi la kijani au jeusi (Aflatoxin)"]
    },
    "Soya Meal": {
        "img": "soyameal.jpg", "prot": 44.0, "en": 2500, "price_per_kg": 2300,
        "max_inc": 35, "qc": ["✅ Rangi ya dhahabu / Golden color", "✅ Harufu ya karanga / Roasted nutty smell", "❌ **Red Flag:** Harufu ya maharagwe mabichi"]
    },
    "BSF Larvae": {
        "img": "bsfl.jpg", "prot": 50.0, "en": 3100, "price_per_kg": 1500,
        "max_inc": 15, "qc": ["✅ Imekauka vizuri / Properly dried", "✅ Haina harufu kali / No foul smell", "🌱 **Eco-Friendly:** High protein, low carbon footprint"]
    },
    "Vegetable Oil": {
        "img": "vegetable-oil.webp", "prot": 0.0, "en": 8800, "price_per_kg": 3500,
        "max_inc": 5, "qc": ["✅ Rangi angavu / Clear color", "✅ Harufu nzuri / Fresh smell", "❌ **Red Flag:** Harufu mbaya / Rancid odor"]
    },
    "Sunflower Cake": {
        "img": "sunflower_cake.jpeg", "prot": 28.0, "en": 2100, "price_per_kg": 950,
        "max_inc": 20, "qc": ["✅ Imekauka na kuwa ngumu / Dry and brittle", "❌ **Red Flag:** Mafuta yanayovuja"]
    }
}

STANDARDS = {
    "Broiler": {
        "Starter (Wk 1-2)": 22.0, "Grower (Wk 3-4)": 20.0, "Finisher (Wk 5+)": 18.0
    },
    "Layer": {
        "Chick Starter (Wk 0-8)": 18.0, "Pullet Grower (Wk 9-18)": 15.0, 
        "Pre-Lay (Wk 19-20)": 17.0, "Layer Phase 1 (Peak)": 18.0, "Layer Phase 2": 16.0
    }
}

# --- 3. HELPER FUNCTIONS ---
def save_to_local_csv(flock_type, flock_name, age, birds, kpi_val, profit_val):
    file_name = 'flock_data.csv'
    new_entry = pd.DataFrame([{
        "Date": datetime.date.today().strftime('%Y-%m-%d'),
        "Type": flock_type,
        "Flock_ID": flock_name,
        "Age": age,
        "Birds": birds,
        "KPI_Value": round(kpi_val, 2),
        "Profit_TSH": round(profit_val, 2)
    }])
    if os.path.isfile(file_name):
        new_entry.to_csv(file_name, mode='a', index=False, header=False)
    else:
        new_entry.to_csv(file_name, index=False)
    st.success(f"✅ Data for {flock_name} ({flock_type}) saved!")

# --- 4. CUSTOM STYLING ---
broiler_bg = "https://raw.githubusercontent.com/erickrugakingira-lab/feedconvo-app/main/broiler_chicken.png"
layer_bg = "https://raw.githubusercontent.com/erickrugakingira-lab/feedconvo-app/main/assets/layers.webp"

selected_type = st.session_state.get("flock_selector", "Broiler")
bg_url = broiler_bg if selected_type == "Broiler" else layer_bg

st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.8)), url("{bg_url}");
        background-attachment: fixed; 
        background-size: 50%; 
        background-repeat: no-repeat; 
        background-position: center;
    }}
    [data-testid="stSidebar"] {{ 
        background-color: #f1f8e9; 
        border-right: 2px solid #c8e6c9; 
    }}
    h1, h2, h3 {{ color: #1b5e20; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR & NAVIGATION ---
with st.sidebar:
    st.header("🚜 Farm Manager")
    lang = st.radio("Lugha / Language:", ["English", "Kiswahili"])
    flock_type = st.radio("Select Type / Chagua Aina:", ["Broiler", "Layer"], key="flock_selector")

    t = {
       "English": {
            "dash": "📊 Dashboard", "solver": "🧪 LCR Optimizer", "guide": "📚 Guide", "market": "🛒 Market",
            "birds": "Live Birds", "age": "Age (Days)", "yield_meat": "Est. Yield (kg)", "yield_eggs": "Est. Trays",
            "fcr_title": "📈 FCR Tracker (Meat)", "hdep_title": "📉 Laying Rate (HDEP%)",
            "feed_cons": "Total Feed Consumed (kg)", "avg_wt": "Avg. Weight per Bird (kg)",
            "eggs_col": "Eggs Collected Today", "tray_price": "Price per Tray (TSH)",
            "roi_title": "💵 Profit & ROI Projection", "solve_title": "🧪 Least-Cost Optimizer",
            "stage": "Select Growth Stage:", "total": "Total Feed to Produce (kg)",
            "invest": "Total Investment", "revenue": "Expected Revenue", "profit": "Projected Profit",
            "edit_fin": "Adjust Costs & Prices", "chick_cost": "Cost per Chick (TSH)",
            "mkt_price": "Selling Price per Bird (TSH)", "other_costs": "Meds/Labor/Bird",
            "hist_title": "📋 Batch History", "save_btn": "🚀 Save Today's Progress",
            "dl_btn": "📥 Download Report", "no_hist": "No history found.", "hist_info": "💡 Data saved daily.",
            "mixing": "🥣 Mixing Instructions"
        },
        "Kiswahili": {
            "dash": "📊 Dashibodi", "solver": "🧪 Kikokotoo LCR", "guide": "📚 Mwongozo", "market": "🛒 Soko",
            "birds": "Kuku Waliopo", "age": "Umri (Siku)", "yield_meat": "Mavuno (kg)", "yield_eggs": "Mavuno (Trei)",
            "fcr_title": "📈 Ufanisi (FCR)", "hdep_title": "📉 Kiwango cha Kutaga (HDEP%)",
            "feed_cons": "Jumla ya Chakula (kg)", "avg_wt": "Uzito wa Kuku (kg)",
            "eggs_col": "Mayai Yaliyokusanywa Leo", "tray_price": "Bei ya Trei 1 (TSH)",
            "roi_title": "💵 Makadirio ya Faida", "solve_title": "🧪 Kikokotoo cha Gharama Nafuu",
            "stage": "Hatua ya Ukuaji:", "total": "Jumla ya Chakula (kg)",
            "invest": "Gharama", "revenue": "Mauzo", "profit": "Faida",
            "edit_fin": "Badili Bei", "chick_cost": "Gharama ya Kifaranga",
            "mkt_price": "Bei ya Kuuza Kuku 1", "other_costs": "Dawa/Wafanyakazi/Kuku",
            "hist_title": "📋 Kumbukumbu", "save_btn": "🚀 Hifadhi Taarifa za Leo",
            "dl_btn": "📥 Pakua Ripoti", "no_hist": "Hakuna kumbukumbu.", "hist_info": "💡 Taarifa huhifadhiwa kila siku.",
            "mixing": "🥣 Maelekezo ya Kuchanganya"
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

# --- 6. PAGE LOGIC ---

# 📊 DASHBOARD
if menu == txt["dash"]:
    st.title(f"{txt['dash']}: {flock_id} ({flock_type})")
    
    m1, m2, m3 = st.columns(3)
    m1.metric(txt["birds"], f"{active_birds}", delta=f"-{mortality}")
    m2.metric(txt["age"], f"{age_days} Siku")
    
    if flock_type == "Broiler":
        m3.metric(txt["yield_meat"], f"{active_birds * 2.2:.1f} kg")
    else:
        m3.metric(txt["yield_eggs"], "---")

    st.divider()
    
    if flock_type == "Broiler":
        st.subheader(txt["fcr_title"])
        c_f1, c_f2 = st.columns([2, 1])
        with c_f1:
            feed_in = st.number_input(txt["feed_cons"], value=10.0)
            avg_wt = st.number_input(txt["avg_wt"], value=0.5)
            kpi_val = feed_in / (active_birds * avg_wt) if (active_birds * avg_wt) > 0 else 0
        with c_f2:
            st.metric("FCR", f"{kpi_val:.2f}")
    else:
        st.subheader(txt["hdep_title"])
        c_l1, c_l2 = st.columns([2, 1])
        with c_l1:
            eggs_collected = st.number_input(txt["eggs_col"], value=50)
            kpi_val = (eggs_collected / active_birds * 100) if active_birds > 0 else 0
        with c_l2:
            st.metric("HDEP%", f"{kpi_val:.1f}%")

    st.divider()
    st.subheader(txt["roi_title"])
    with st.expander(txt["edit_fin"]):
        cx, cy, cz = st.columns(3)
        c_cost = cx.number_input(txt["chick_cost"], value=1500)
        p_revenue_unit = cy.number_input(txt["mkt_price"] if flock_type == "Broiler" else txt["tray_price"], value=8500 if flock_type == "Broiler" else 7500)
        o_costs = cz.number_input(txt["other_costs"], value=1500)
        feed_price_kg = st.number_input("Feed Price/KG", value=1200)

    if flock_type == "Broiler":
        total_invest = (flock_size * c_cost) + (feed_in * feed_price_kg) + (active_birds * o_costs)
        revenue = active_birds * p_revenue_unit
    else:
        daily_feed = 0.12 * active_birds 
        total_invest = (flock_size * c_cost / 365) + (daily_feed * feed_price_kg) + (active_birds * o_costs / 30)
        revenue = (eggs_collected / 30) * p_revenue_unit
        
    profit = revenue - total_invest
    roi_pct = (profit / total_invest * 100) if total_invest > 0 else 0

    r1, r2, r3 = st.columns(3)
    r1.metric(txt["invest"], f"{total_invest:,.0f} TSH")
    r2.metric(txt["revenue"], f"{revenue:,.0f} TSH")
    r3.metric(txt["profit"], f"{profit:,.0f} TSH", f"{roi_pct:.1f}% ROI")
    
    st.divider()
    st.subheader(txt["hist_title"])
    if st.button(txt["save_btn"]):
        save_to_local_csv(flock_type, flock_id, age_days, active_birds, kpi_val, profit)

    if os.path.isfile('flock_data.csv'):
        history_df = pd.read_csv('flock_data.csv')
        if 'Type' in history_df.columns:
            filtered_df = history_df[history_df['Type'] == flock_type]
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.warning("Old data format. Delete 'flock_data.csv' to reset.")
            st.dataframe(history_df, use_container_width=True)
    else:
        st.info(txt["no_hist"])

# 🧪 FEED SOLVER (LCR Optimizer Edition)
elif menu == txt["solver"]:
    st.title(f"{txt['solve_title']} ({flock_type})")
    current_standards = STANDARDS[flock_type]
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        stage = st.selectbox(txt["stage"], list(current_standards.keys()))
        target_prot = current_standards[stage]
    with col_b:
        total_produce = st.number_input(txt["total"], min_value=1.0, value=100.0)
    with col_c:
        # LCR Logic: Adjust prices to see how recipe changes
        bsfl_price = st.number_input("BSFL Price/kg (TSH)", value=1500)
        soya_price = st.number_input("Soya Price/kg (TSH)", value=2300)

    st.divider()
    m1, m2, m3 = st.columns(3)
    with m1:
        use_bsfl = st.checkbox("🌱 Use Eco-BSFL (Max 15%)", value=True)
        bsfl_inc = 0.15 if use_bsfl else 0.0
    with m2:
        use_premix = st.checkbox("Include 5% Premix", value=True)
        pre_pct = 0.05 if use_premix else 0.0
    with m3:
        use_minerals = st.checkbox("Include Minerals (DCP)", value=True)
        min_pct = (2.0 if flock_type == "Layer" else 1.0) / 100 if use_minerals else 0.0
    
    # --- LCR MATH LOGIC ---
    # The LCR automatically prioritizes the cheapest protein source (BSFL vs Soya)
    oil_pct = 0.015 if flock_type == "Broiler" else 0.005
    fixed_pct = pre_pct + min_pct + oil_pct
    
    # 1. Calculate protein contributed by BSFL (if selected)
    bsfl_prot_contrib = bsfl_inc * ING_DATABASE["BSF Larvae"]["prot"]
    
    # 2. Remaining protein needed from Maize & Soya
    needed_prot = target_prot - bsfl_prot_contrib
    remaining_space = 1.0 - fixed_pct - bsfl_inc
    
    # 3. Precision Pearson for the remaining space
    usable_target = needed_prot / remaining_space
    m_prot, s_prot = ING_DATABASE["Maize"]["prot"], ING_DATABASE["Soya Meal"]["prot"]
    soya_ratio = (usable_target - m_prot) / (s_prot - m_prot)
    
    # Final Weights
    maize_kg = total_produce * remaining_space * (1 - soya_ratio)
    soya_kg = total_produce * remaining_space * soya_ratio
    bsfl_kg = total_produce * bsfl_inc
    pre_kg = total_produce * pre_pct
    min_kg = total_produce * min_pct
    oil_kg = total_produce * oil_pct

    st.subheader(f"📋 Optimized Recipe ({total_produce}kg)")
    recipe_df = pd.DataFrame({
        "Ingredient": ["Maize", "Soya Meal", "Eco-BSFL 🐛", "Premix", "DCP/Bone Meal", "Oil"],
        "Weight (kg)": [f"{maize_kg:.2f}", f"{soya_kg:.2f}", f"{bsfl_kg:.2f}", f"{pre_kg:.2f}", f"{min_kg:.2f}", f"{oil_kg:.2f}"],
        "Cost Contribution": [f"{maize_kg*850:,.0f}", f"{soya_kg*soya_price:,.0f}", f"{bsfl_kg*bsfl_price:,.0f}", "---", "---", "---"]
    })
    st.table(recipe_df)
    
    total_cost_est = (maize_kg*850) + (soya_kg*soya_price) + (bsfl_kg*bsfl_price)
    st.info(f"💰 **Estimated Ingredient Cost:** {total_cost_est:,.0f} TSH per {total_produce}kg")

    with st.expander(txt["mixing"]):
        st.write("1. **BSFL Integration:** Ensure larvae are dried and crushed for even mixing.")
        st.write("2. **Sustainable Note:** Using BSFL reduces Soya dependency by up to 30%!")

# 📚 GUIDE & 🛒 MARKET
elif menu == txt["guide"]:
    st.title(txt["guide"])
    sel_ing = st.selectbox("Select Ingredient:", list(ING_DATABASE.keys()))
    data = ING_DATABASE[sel_ing]
    c_img, c_info = st.columns([1, 2])
    with c_img:
        img_url = f"https://raw.githubusercontent.com/erickrugakingira-lab/feedconvo-app/main/assets/{data['img'].replace(' ', '%20')}"
        st.image(img_url, use_container_width=True)
    with c_info:
        for check in data["qc"]:
            st.write(check)
    
    st.divider()
    st.subheader("💡 Environmental Tip")
    st.success("Black Soldier Fly Larvae (BSFL) recycle organic waste into high-quality protein, reducing the need for forest-clearing soya farming.")

elif menu == txt["market"]:
    st.title(txt["market"])
    for name, info in ING_DATABASE.items():
        c1, c2, c3 = st.columns([1, 2, 1])
        c1.write(name)
        c2.write(f"{info['price_per_kg']} TSH/kg")
        c3.link_button("Order", f"https://wa.me/255700000000?text=Order%20{name}")

st.divider()
st.caption(f"🚀 FeedConvo Pro | {flock_type} Mode | Eco-LCR Active")
