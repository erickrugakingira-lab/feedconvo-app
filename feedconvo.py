import streamlit as st
import pandas as pd
import datetime
import os

# --- 1. GLOBAL CONFIGURATION ---
st.set_page_config(page_title="FeedConvo Poultry Pro", layout="wide", page_icon="🐔")

# --- 2. THE DATABASES ---
ING_DATABASE = {
    "Maize": {
        "img": "maize_grain.jpg", "prot": 9.0, "en": 3350, "price_per_kg": 850,
        "qc": [
            "✅ Unyevu < 13% (Usinunue mahindi mabichi) / Moisture < 13%",
            "✅ Nafaka nzima, zisizo na matundu ya wadudu / Whole grains",
            "❌ **Red Flag:** Vumbi la kijani au jeusi (Aflatoxin) / Green or black dust"
        ]
    },
    "Soya Meal": {
        "img": "soyameal.jpg", "prot": 44.0, "en": 2500, "price_per_kg": 2300,
        "qc": [
            "✅ Rangi ya dhahabu iliyokoza / Deep golden color",
            "✅ Harufu ya karanga zilizokaangwa / Roasted nutty smell",
            "❌ **Red Flag:** Harufu ya maharagwe mabichi / Raw bean smell (Toxic)"
        ]
    },
    "Vegetable Oil": {
        "img": "vegetable_oil.jpg", "prot": 0.0, "en": 8800, "price_per_kg": 3500,
        "qc": [
            "✅ Rangi angavu, haina vumbi / Clear color, no sediment",
            "✅ Harufu nzuri / Fresh smell",
            "❌ **Red Flag:** Harufu mbaya ya kukaa muda mrefu / Strong rancid odor"
        ]
    },
    "Sunflower Cake": {
        "img": "sunflower_cake.jpeg", "prot": 28.0, "en": 2100, "price_per_kg": 950,
        "qc": [
            "✅ Imekauka na kuwa ngumu / Dry and brittle",
            "❌ **Red Flag:** Mafuta yanayovuja (Inaharibika haraka) / Leaking oil"
        ]
    }
}

STANDARDS = {
    "Starter (Wk 1-2)": 22.0, 
    "Grower (Wk 3-4)": 20.0, 
    "Finisher (Wk 5+)": 18.0
}

# --- 3. CUSTOM STYLING ---
bg_url = "https://raw.githubusercontent.com/erickrugakingira-lab/feedconvo-app/main/broiler_chicken.png"
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(255, 255, 255, 0.75), rgba(255, 255, 255, 0.75)), url("{bg_url}");
        background-attachment: fixed; background-size: contain; background-repeat: no-repeat; background-position: center bottom;
    }}
    [data-testid="stSidebar"] {{ background-color: #e8f5e9; border-right: 2px solid #c8e6c9; }}
    h1, h2, h3 {{ color: #1b5e20; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR & NAVIGATION ---
with st.sidebar:
    st.header("🚜 Farm Manager")
    lang = st.radio("Lugha / Language:", ["English", "Kiswahili"])
    
    t = {
       "English": {
            "dash": "📊 Dashboard", "solver": "🧪 Feed Solver", "guide": "📚 Guide", "market": "🛒 Market",
            "birds": "Live Birds", "age": "Age (Days)", "yield": "Est. Yield (kg)",
            "fcr_title": "📈 FCR Tracker", "feed_cons": "Total Feed Consumed (kg)",
            "avg_wt": "Avg. Weight per Bird (kg)", "roi_title": "💵 Profit & ROI Projection",
            "solve_title": "🧪 Precision Feed Solver", "stage": "Select Growth Stage:",
            "total": "Total Feed to Produce (kg)", "download": "📥 Download Recipe", 
            "mixing": "🥣 Mixing Instructions", "invest": "Total Investment", 
            "revenue": "Expected Revenue", "profit": "Projected Profit",
            "edit_fin": "Adjust Costs & Prices", "chick_cost": "Cost per Chick (TSH)",
            "mkt_price": "Selling Price per Bird (TSH)", "other_costs": "Meds/Labor per Bird (TSH)"
        },
        "Kiswahili": {
            "dash": "📊 Dashibodi", "solver": "🧪 Kikokotoo", "guide": "📚 Mwongozo", "market": "🛒 Soko",
            "birds": "Kuku Waliopo", "age": "Umri (Siku)", "yield": "Mavuno (kg)",
            "fcr_title": "📈 Ufanisi (FCR)", "feed_cons": "Jumla ya Chakula (kg)",
            "avg_wt": "Uzito wa Kuku (kg)", "roi_title": "💵 Makadirio ya Faida",
            "solve_title": "🧪 Kikokotoo cha Chakula",
            "stage": "Hatua ya Ukuaji:", "total": "Jumla ya Chakula (kg)",
            "download": "📥 Pakua Maelekezo", "mixing": "🥣 Maelekezo ya Kuchanganya",
            "invest": "Gharama", "revenue": "Mauzo", 
            "profit": "Faida", "edit_fin": "Badili Bei", 
            "chick_cost": "Gharama ya Kifaranga", "mkt_price": "Bei ya Kuuza Kuku 1", 
            "other_costs": "Dawa/Wafanyakazi kwa kila Kuku"
        }
    }
    txt = t[lang]
    menu = st.radio("GO TO:", [txt["dash"], txt["solver"], txt["guide"], txt["market"]])
    
    st.divider()
    flock_id = st.text_input("Flock ID", value="Batch-001")
    flock_size = st.number_input("Total Birds", min_value=1, value=100)
    mortality = st.number_input("Mortality", min_value=0, value=0)
    start_date = st.date_input("Hatch Date", datetime.date.today() - datetime.timedelta(days=14))
    
    # Global Calculations
    active_birds = max(0, flock_size - mortality)
    age_days = (datetime.date.today() - start_date).days

# --- 5. PAGE LOGIC ---

# 📊 DASHBOARD
if menu == txt["dash"]:
    st.title(f"{txt['dash']}: {flock_id}")
    
    m1, m2, m3 = st.columns(3)
    m1.metric(txt["birds"], f"{active_birds}", delta=f"-{mortality} vifo")
    m2.metric(txt["age"], f"{age_days} Siku")
    m3.metric(txt["yield"], f"{active_birds * 2.2:.1f} kg")

    st.divider()
    st.subheader(txt["fcr_title"])
    c_f1, c_f2 = st.columns([2, 1])
    with c_f1:
        feed_in = st.number_input(txt["feed_cons"], value=10.0)
        avg_wt = st.number_input(txt["avg_wt"], value=0.5)
        fcr = feed_in / (active_birds * avg_wt) if (active_birds * avg_wt) > 0 else 0
    with c_f2:
        st.metric("FCR", f"{fcr:.2f}")

    st.divider()
    st.subheader(txt["roi_title"])
    with st.expander(txt["edit_fin"]):
        cx, cy, cz = st.columns(3)
        c_cost = cx.number_input(txt["chick_cost"], value=1500)
        p_per_bird = cy.number_input(txt["mkt_price"], value=8500)
        o_costs = cz.number_input(txt["other_costs"], value=1500)
        feed_price_kg = st.number_input("Feed Cost per KG", value=1200)

    total_invest = (flock_size * c_cost) + (feed_in * feed_price_kg) + (active_birds * o_costs)
    revenue = active_birds * p_per_bird
    profit = revenue - total_invest
    roi_pct = (profit / total_invest * 100) if total_invest > 0 else 0

    r1, r2, r3 = st.columns(3)
    r1.metric(txt["invest"], f"{total_invest:,.0f} TSH")
    r2.metric(txt["revenue"], f"{revenue:,.0f} TSH")
    r3.metric(txt["profit"], f"{profit:,.0f} TSH", f"{roi_pct:.1f}% ROI", delta_color="normal" if profit > 0 else "inverse")

    # VACCINATION TABLE
    st.divider()
    st.subheader("💉 Vaccination Schedule")
    h_day, h_vac, h_stat = "Day", "Vaccine", "Status"
    done = "✅ Done" if lang == "English" else "✅ Imekamilika"
    pending = "⏳ Pending" if lang == "English" else "⏳ Inasubiri"
    vac_data = {
        h_day: [1, 7, 14, 21, 28, 35],
        h_vac: ["Marek's/IB", "Gumboro 1", "Newcastle 1", "Gumboro 2", "Newcastle 2", "Fowl Pox"],
        h_stat: [done if age_days >= d else pending for d in [1, 7, 14, 21, 28, 35]]
    }
    st.table(pd.DataFrame(vac_data))

# 🧪 FEED SOLVER
elif menu == txt["solver"]:
    st.title(txt["solve_title"])
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        stage = st.selectbox(txt["stage"], list(STANDARDS.keys()))
        target_prot = STANDARDS[stage]
    with col_b:
        total_produce = st.number_input(txt["total"], min_value=1.0, value=100.0)
    with col_c:
        oil_pct = st.slider("Oil % (Energy)", 0.0, 3.0, 1.0) / 100

    use_premix = st.checkbox("Include 5% Premix", value=True)
    premix_pct = 0.05 if use_premix else 0.0
    
    # Pearson Square Math
    remaining_pct = 1.0 - oil_pct - premix_pct
    usable_target = target_prot / remaining_pct
    m_prot, s_prot = ING_DATABASE["Maize"]["prot"], ING_DATABASE["Soya Meal"]["prot"]
    soya_ratio = (usable_target - m_prot) / (s_prot - m_prot)
    
    maize_kg = total_produce * remaining_pct * (1 - soya_ratio)
    soya_kg = total_produce * remaining_pct * soya_ratio
    oil_kg = total_produce * oil_pct
    pre_kg = total_produce * premix_pct

    st.subheader(f"📋 Recipe ({total_produce}kg)")
    recipe_df = pd.DataFrame({
        "Ingredient": ["Maize", "Soya Meal", "Vegetable Oil", "Premix"],
        "Weight (kg)": [f"{maize_kg:.2f}", f"{soya_kg:.2f}", f"{oil_kg:.2f}", f"{pre_kg:.2f}"]
    })
    st.table(recipe_df)
    
    with st.expander(txt["mixing"]):
        if lang == "Kiswahili":
            st.write(f"1. **Mafuta:** Sugua {oil_kg:.1f}kg za mafuta kwenye kiasi kidogo cha mahindi.")
            st.write("2. **Mchanganyiko:** Tandaza mahindi, kisha soya, kisha premix.")
            st.write("3. **Geuza:** Tumia jembe kugeuza rundo mara 3.")
        else:
            st.write(f"1. **Oil Rub:** Rub {oil_kg:.1f}kg of oil into a small batch of maize first.")
            st.write("2. **Layering:** Layer Maize, then Soya, then Premix.")
            st.write("3. **Turn:** Turn 3 times with a shovel.")

# 📚 GUIDE
elif menu == txt["guide"]:
    st.title(txt["guide"])
    sel_ing = st.selectbox("Select Ingredient:", list(ING_DATABASE.keys()))
    data = ING_DATABASE[sel_ing]
    c_img, c_info = st.columns([1, 2])
    with c_img:
        url = f"https://raw.githubusercontent.com/erickrugakingira-lab/feedconvo-app/main/assets/{data['img'].replace(' ', '%20')}"
        st.image(url, use_container_width=True)
    with c_info:
        st.subheader(f"🔍 {sel_ing} Quality Checks")
        for check in data["qc"]:
            if "✅" in check: st.success(check)
            else: st.error(check)
        st.write(f"**Protein:** {data['prot']}% | **Energy:** {data['en']} kcal/kg")

# 🛒 MARKET
elif menu == txt["market"]:
    st.title(txt["market"])
    for name, info in ING_DATABASE.items():
        c1, c2, c3 = st.columns([1, 2, 1])
        c1.subheader(name)
        c2.write(f"**Price:** {info['price_per_kg']} TSH/kg")
        wa_link = f"https://wa.me/255700000000?text=I%20want%20to%20order%20{name}"
        c3.link_button(f"Order {name}", wa_link, type="primary")
        st.divider()

st.caption("🚀 Powered by FeedConvo Local Logistics")
           
