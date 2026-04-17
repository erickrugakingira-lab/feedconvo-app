import streamlit as st
import pandas as pd
import datetime
import os

# --- 1. GLOBAL CONFIGURATION ---
st.set_page_config(
    page_title="FeedConvo Pro", 
    layout="wide", 
    initial_sidebar_state="expanded", 
    page_icon="https://raw.githubusercontent.com/erickrugakingira-lab/feedconvo-app/main/assets/Main_logo.png" # Updated to your logo
)

# --- 2. THE DATABASES ---
ING_DATABASE = {
    "Maize": {
        "img": "maize_grain.jpg", "prot": 9.0, "en": 3350, "price_per_kg": 850,
        "qc": ["✅ Unyevu < 13% / Moisture < 13%", "✅ Nafaka nzima / Whole grains", "❌ **Red Flag:** Vumbi la kijani au jeusi (Aflatoxin)"]
    },
    "Soya Meal": {
        "img": "soyameal.jpg", "prot": 44.0, "en": 2500, "price_per_kg": 2300,
        "qc": ["✅ Rangi ya dhahabu / Golden color", "✅ Harufu ya karanga / Roasted nutty smell", "❌ **Red Flag:** Harufu ya maharagwe mabichi"]
    },
    "Vegetable Oil": {
        "img": "vegetable-oil.webp", "prot": 0.0, "en": 8800, "price_per_kg": 3500,
        "qc": ["✅ Rangi angavu / Clear color", "✅ Harufu nzuri / Fresh smell", "❌ **Red Flag:** Harufu mbaya / Rancid odor"]
    },
    "Sunflower Cake": {
        "img": "sunflower_cake.jpeg", "prot": 28.0, "en": 2100, "price_per_kg": 950,
        "qc": ["✅ Imekauka na kuwa ngumu / Dry and brittle", "❌ **Red Flag:** Mafuta yanayovuja"]
    }
}

# STANDARDS (Now Split by Flock Type)
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
    file_name = f'flock_data.csv'
    new_entry = pd.DataFrame([{
        "Date": datetime.date.today().strftime('%Y-%m-%d'),
        "Type": flock_type,
        "Flock_ID": flock_name,
        "Age": age,
        "Birds": birds,
        "KPI_Value": round(kpi_val, 2), # FCR for Broilers, HDEP for Layers
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

# 1. Check session state Safely. If it's the first run, default to Broiler.
selected_type = st.session_state.get("flock_selector", "Broiler")
bg_url = broiler_bg if selected_type == "Broiler" else layer_bg

st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.58), url("{bg_url}");
        background-attachment: fixed; 
        background-size: contain; 
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
    
    # 2. Add the radio button with the key "flock_selector"
    # We add on_change to force the app to rerun and apply the new CSS immediately
    flock_type = st.radio(
        "Select Type / Chagua Aina:", 
        ["Broiler", "Layer"], 
        key="flock_selector"
    )
    t = {
       "English": {
            "dash": "📊 Dashboard", "solver": "🧪 Feed Solver", "guide": "📚 Guide", "market": "🛒 Market",
            "birds": "Live Birds", "age": "Age (Days)", "yield_meat": "Est. Yield (kg)", "yield_eggs": "Est. Trays",
            "fcr_title": "📈 FCR Tracker (Meat)", "hdep_title": "📉 Laying Rate (HDEP%)",
            "feed_cons": "Total Feed Consumed (kg)", "avg_wt": "Avg. Weight per Bird (kg)",
            "eggs_col": "Eggs Collected Today", "tray_price": "Price per Tray (TSH)",
            "roi_title": "💵 Profit & ROI Projection", "solve_title": "🧪 Precision Feed Solver",
            "stage": "Select Growth Stage:", "total": "Total Feed to Produce (kg)",
            "invest": "Total Investment", "revenue": "Expected Revenue", "profit": "Projected Profit",
            "edit_fin": "Adjust Costs & Prices", "chick_cost": "Cost per Chick (TSH)",
            "mkt_price": "Selling Price per Bird (TSH)", "other_costs": "Meds/Labor/Bird",
            "hist_title": "📋 Batch History", "save_btn": "🚀 Save Today's Progress",
            "dl_btn": "📥 Download Report", "no_hist": "No history found.", "hist_info": "💡 Data saved daily."
        },
        "Kiswahili": {
            "dash": "📊 Dashibodi", "solver": "🧪 Kikokotoo", "guide": "📚 Mwongozo", "market": "🛒 Soko",
            "birds": "Kuku Waliopo", "age": "Umri (Siku)", "yield_meat": "Mavuno (kg)", "yield_eggs": "Mavuno (Trei)",
            "fcr_title": "📈 Ufanisi (FCR)", "hdep_title": "📉 Kiwango cha Kutaga (HDEP%)",
            "feed_cons": "Jumla ya Chakula (kg)", "avg_wt": "Uzito wa Kuku (kg)",
            "eggs_col": "Mayai Yaliyokusanywa Leo", "tray_price": "Bei ya Trei 1 (TSH)",
            "roi_title": "💵 Makadirio ya Faida", "solve_title": "🧪 Kikokotoo cha Chakula",
            "stage": "Hatua ya Ukuaji:", "total": "Jumla ya Chakula (kg)",
            "invest": "Gharama", "revenue": "Mauzo", "profit": "Faida",
            "edit_fin": "Badili Bei", "chick_cost": "Gharama ya Kifaranga",
            "mkt_price": "Bei ya Kuuza Kuku 1", "other_costs": "Dawa/Wafanyakazi/Kuku",
            "hist_title": "📋 Kumbukumbu", "save_btn": "🚀 Hifadhi Taarifa za Leo",
            "dl_btn": "📥 Pakua Ripoti", "no_hist": "Hakuna kumbukumbu.", "hist_info": "💡 Taarifa huhifadhiwa kila siku."
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
    
    # Logic for Yield Display
    if flock_type == "Broiler":
        m3.metric(txt["yield_meat"], f"{active_birds * 2.2:.1f} kg")
    else:
        m3.metric(txt["yield_eggs"], "---")

    st.divider()
    
    # Logic for Performance Tracking
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

    # ROI Calculation
    st.divider()
    st.subheader(txt["roi_title"])
    with st.expander(txt["edit_fin"]):
        cx, cy, cz = st.columns(3)
        c_cost = cx.number_input(txt["chick_cost"], value=1500)
        
        if flock_type == "Broiler":
            p_revenue_unit = cy.number_input(txt["mkt_price"], value=8500)
        else:
            p_revenue_unit = cy.number_input(txt["tray_price"], value=7500)
            
        o_costs = cz.number_input(txt["other_costs"], value=1500)
        feed_price_kg = st.number_input("Feed Price/KG", value=1200)

    # Financial Math
    if flock_type == "Broiler":
        total_invest = (flock_size * c_cost) + (feed_in * feed_price_kg) + (active_birds * o_costs)
        revenue = active_birds * p_revenue_unit
    else:
        # Layer assumption: Daily feed cost vs daily egg revenue
        daily_feed = 0.12 * active_birds # 120g per bird
        total_invest = (flock_size * c_cost / 365) + (daily_feed * feed_price_kg) + (active_birds * o_costs / 30)
        revenue = (eggs_collected / 30) * p_revenue_unit
        
    profit = revenue - total_invest
    roi_pct = (profit / total_invest * 100) if total_invest > 0 else 0

    r1, r2, r3 = st.columns(3)
    r1.metric(txt["invest"], f"{total_invest:,.0f} TSH")
    r2.metric(txt["revenue"], f"{revenue:,.0f} TSH")
    r3.metric(txt["profit"], f"{profit:,.0f} TSH", f"{roi_pct:.1f}% ROI")
    
  # BATCH HISTORY SECTION
    st.divider()
    st.subheader(txt["hist_title"])
    if st.button(txt["save_btn"]):
        save_to_local_csv(flock_type, flock_id, age_days, active_birds, kpi_val, profit)

    if os.path.isfile('flock_data.csv'):
        history_df = pd.read_csv('flock_data.csv')
        
        # Check if 'Type' column exists to avoid the KeyError
        if 'Type' in history_df.columns:
            filtered_df = history_df[history_df['Type'] == flock_type]
            if not filtered_df.empty:
                st.dataframe(filtered_df, use_container_width=True)
            else:
                st.info(txt["no_hist"])
        else:
            # If the file is old, just show the whole thing or tell user to reset
            st.warning("Old data format detected. Please delete 'flock_data.csv' to reset.")
            st.dataframe(history_df, use_container_width=True)
    else:
        st.info(txt["no_hist"])
        
# 🧪 FEED SOLVER (Dynamic)
elif menu == txt["solver"]:
    st.title(f"{txt['solve_title']} ({flock_type})")
    current_standards = STANDARDS[flock_type]
    
    col_a, col_b = st.columns(2)
    with col_a:
        stage = st.selectbox(txt["stage"], list(current_standards.keys()))
        target_prot = current_standards[stage]
    with col_b:
        total_produce = st.number_input(txt["total"], min_value=1.0, value=100.0)

    # Pearson Square Math (Simplified)
    m_prot, s_prot = ING_DATABASE["Maize"]["prot"], ING_DATABASE["Soya Meal"]["prot"]
    soya_ratio = (target_prot - m_prot) / (s_prot - m_prot)
    
    maize_kg = total_produce * (1 - soya_ratio)
    soya_kg = total_produce * soya_ratio

    st.subheader(f"📋 Recipe: {stage}")
    st.table(pd.DataFrame({"Ingredient": ["Maize", "Soya Meal"], "Weight (kg)": [f"{maize_kg:.2f}", f"{soya_kg:.2f}"]}))

# 📚 GUIDE & 🛒 MARKET 
elif menu == txt["guide"]:
    st.title(txt["guide"])
    
    # Select Ingredient to see Quality Control tips
    sel_ing = st.selectbox("Select Ingredient / Chagua Kiambata:", list(ING_DATABASE.keys()))
    data = ING_DATABASE[sel_ing]
    
    c_img, c_info = st.columns([1, 2])
    
    with c_img:
        # Note: Ensure these images exist in your GitHub assets folder
        img_url = f"https://raw.githubusercontent.com/erickrugakingira-lab/feedconvo-app/main/assets/{data['img'].replace(' ', '%20')}"
        st.image(img_url, use_container_width=True, caption=sel_ing)
        
    with c_info:
        st.subheader(f"🔍 {sel_ing}: Quality Checks")
        for check in data["qc"]:
            if "✅" in check:
                st.success(check)
            else:
                st.error(check)
        
        # Display Nutritional Values
        st.info(f"**Protein:** {data['prot']}% | **Energy:** {data['en']} kcal/kg")

    # NEW: Layer vs Broiler Specific Management Tips
    st.divider()
    st.subheader("💡 Pro Management Tips")
    if flock_type == "Broiler":
        st.write("• **Lighting:** 23 hours of light for the first 7 days to encourage feeding.")
        st.write("• **Temperature:** Keep brooder at 32°C-35°C in week 1.")
    else:
        st.write("• **Calcium:** Layers need high calcium (Oyster shells) once they start laying.")
        st.write("• **Nests:** Provide 1 nesting box for every 5 hens to prevent floor eggs.")

# --- 8. RESTORED: MARKET SECTION ---
elif menu == txt["market"]:
    st.title(txt["market"])
    st.markdown(f"### 🛒 Connect with Suppliers for {flock_type} Farming")
    
    # Display ingredients with order buttons
    for name, info in ING_DATABASE.items():
        with st.container():
            c1, c2, c3 = st.columns([1, 2, 1])
            c1.subheader(name)
            c2.write(f"**Current Price:** {info['price_per_kg']} TSH/kg")
            
            # Dynamic WhatsApp Link
            message = f"Hello, I am using FeedConvo Pro. I would like to order {name} for my {flock_type} batch."
            wa_link = f"https://wa.me/255700000000?text={message.replace(' ', '%20')}"
            
            c3.link_button(f"Order {name}", wa_link, type="primary")
            st.divider()

    # Add a section for selling the end product
    st.subheader("🏁 Market Your Harvest")
    if flock_type == "Broiler":
        st.write("Connect with chicken wholesalers and hotels in Tanzania.")
        st.button("List my Broilers for Sale")
    else:
        st.write("Sell your egg trays to local retailers and supermarkets.")
        st.button("List my Egg Trays for Sale")

# --- FOOTER ---
st.divider()
st.caption(f"🚀 FeedConvo Pro | {flock_type} Management Mode | Dar es Salaam, TZ")
