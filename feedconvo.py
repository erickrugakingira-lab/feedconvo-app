import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import os

# --- 1. GLOBAL CONFIGURATION ---
st.set_page_config(page_title="FeedConvo Poultry Pro", layout="wide", page_icon="🐔")

# --- 2. THE DATABASES (Global Scope) ---
ING_DATABASE = {
    "Maize": {
        "img": "maize_grain.jpg", "prot": 9.0, "en": 3350, "price_per_kg": 850,
        "qc": [
            "✅ Unyevu < 13% (Usinunue mahindi mabichi) / Moisture < 13%",
            "✅ Nafaka nzima, zisizo na matundu ya wadudu / Whole grains, no weevil holes",
            "✅ Harufu nzuri ya shambani / Fresh farm smell",
            "❌ **Red Flag:** Vumbi la kijani au jeusi (Aflatoxin) / Green or black dust",
            "❌ **Red Flag:** Harufu ya uvundo/nyevunyevu / Musty or damp smell"
        ]
    },
    "Soya Meal": {
        "img": "soyameal.jpg", "prot": 44.0, "en": 2500, "price_per_kg": 2300,
        "qc": [
            "✅ Rangi ya dhahabu iliyokoza / Deep golden color",
            "✅ Harufu ya karanga zilizokaangwa / Roasted nutty smell",
            "✅ Unyevu mdogo, haishikani mkono / Low moisture, doesn't clump",
            "❌ **Red Flag:** Rangi nyeupe (haijapikwa vizuri) / White color (under-processed)",
            "❌ **Red Flag:** Harufu ya maharagwe mabichi / Raw bean smell (Toxic to birds)"
        ]
    },
    "Fish Meal": {
        "img": "fishmeal.jpg", "prot": 55.0, "en": 2800, "price_per_kg": 3500,
        "qc": [
            "✅ Harufu ya samaki (si ya kioza) / Clean fishy smell",
            "✅ Rangi ya kahawia iliyokoza / Dark brown color",
            "✅ Haina mchanga chini ya gunia / No sand grit at bottom",
            "❌ **Red Flag:** Mabonge makubwa ya chumvi / Large salt clumps",
            "❌ **Red Flag:** Harufu ya kemikali au kioza / Chemical or rotten smell"
        ]
    },
    "Sunflower Cake": {
        "img": "sunflower_cake.jpeg", "prot": 28.0, "en": 2100, "price_per_kg": 950,
        "qc": [
            "✅ Imekauka na kuwa ngumu / Dry and brittle texture",
            "✅ Maganda yamesagwa vizuri / Hulls are finely ground",
            "❌ **Red Flag:** Mafuta yanayovuja (Inaharibika haraka) / Leaking oil (Goes rancid)",
            "❌ **Red Flag:** Uwepo wa nyuzi za magunia / Presence of gunny bag fibers"
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
        background: linear-gradient(rgba(255, 255, 255, 0.70), rgba(255, 255, 255, 0.70)), url("{bg_url}");
        background-attachment: fixed;
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center bottom;
    }}
    .main {{ 
        background-color: #ffffff; 
        padding: 40px; 
        border-radius: 20px;
        box-shadow: 0 15px 50px rgba(0,0,0,0.1);
        margin-top: 30px;
        border: 1px solid #e0e0e0;
    }}
    [data-testid="stSidebar"] {{
        background-color: #e8f5e9; 
        border-right: 2px solid #c8e6c9;
    }}
    h1, h2, h3 {{ color: #1b5e20; }}
    </style>
    """, unsafe_allow_html=True)
    
# --- 4. SIDEBAR & LANGUAGE LOGIC ---
with st.sidebar:
    st.header("🚜 Farm Manager")
    lang = st.radio("Chagua Lugha / Select Language:", ["English", "Kiswahili"])
    
    st.divider()
    
    t = {
       "English": {
            "dash": "📊 Dashboard", "solver": "🧪 Feed Solver", "guide": "📚 Guide", "market": "🛒 Market",
            "birds": "Live Birds", "age": "Age (Days)", "yield": "Est. Yield (kg)",
            "fcr_title": "📈 FCR Tracker (Efficiency)", "feed_cons": "Total Feed Consumed (kg)",
            "avg_wt": "Current Avg. Weight per Bird (kg)", "roi_title": "💵 Profit & ROI Projection",
            "solve_title": "🧪 Precision Feed Solver", "stage": "Select Growth Stage:",
            "total": "Total Feed to Produce (kg)", "download": "📥 Download Recipe", 
            "mixing": "🥣 Mixing Instructions", "invest": "Total Investment", 
            "revenue": "Expected Revenue", "profit": "Projected Profit",
            "edit_fin": "Adjust Costs & Prices", "chick_cost": "Cost per Chick (TSH)",
            "mkt_price": "Market Price per Bird (TSH)", "other_costs": "Other Costs (Meds, Labor)"
        },
        "Kiswahili": {
            "dash": "📊 Dashibodi", "solver": "🧪 Kikokotoo", "guide": "📚 Mwongozo", "market": "🛒 Soko",
            "birds": "Kuku Waliopo", "age": "Umri (Siku)", "yield": "Mavuno (kg)",
            "fcr_title": "📈 Ufanisi wa Chakula (FCR)", "feed_cons": "Jumla ya Chakula (kg)",
            "avg_wt": "Wastani wa Uzito wa Kuku (kg)", "roi_title": "💵 Makadirio ya Faida (ROI)",
            "solve_title": "🧪 Kikokotoo cha Chakula",
            "stage": "Chagua Hatua ya Ukuaji:", "total": "Jumla ya Chakula (kg)",
            "download": "📥 Pakua Maelekezo", "mixing": "🥣 Maelekezo ya Kuchanganya",
            "invest": "Jumla ya Gharama", "revenue": "Mauzo Yanayotarajiwa", 
            "profit": "Faida Inayotarajiwa", "edit_fin": "Badili Gharama na Bei", 
            "chick_cost": "Gharama ya Kifaranga (TSH)", "mkt_price": "Bei ya Kuuza Kuku 1 (TSH)", 
            "other_costs": "Gharama Nyingine (Dawa, Mkaa)"
        }
    }

    txt = t[lang]
    menu = st.radio("GO TO:", [txt["dash"], txt["solver"], txt["guide"], txt["market"]])
    
    st.divider()
    st.subheader("🆔 Flock Identity")
    flock_id = st.text_input("Flock ID", value="Batch-001")
    
    st.subheader("🐣 Bird Data")
    flock_size = st.number_input("Total Birds", min_value=1, value=100)
    mortality = st.number_input("Mortality", min_value=0, value=0)
    start_date = st.date_input("Hatch Date", datetime.date.today() - datetime.timedelta(days=14))

    # Calculate global variables needed for the app
    active_birds = max(0, flock_size - mortality)
    age_days = (datetime.date.today() - start_date).days
    total_potential_yield = active_birds * 2.5 # Assuming 2.5kg target

# --- 5. PAGE LOGIC ---

if menu == txt["dash"]:
    st.title(f"{txt['dash']}: {flock_id}")
    
    m1, m2, m3 = st.columns(3)
    m1.metric(txt["birds"], f"{active_birds}", delta=f"-{mortality} deaths", delta_color="inverse")
    m2.metric(txt["age"], f"{age_days} Days")
    m3.metric(txt["yield"], f"{total_potential_yield:.1f} kg")

    st.divider()

    # FCR Tracker
    st.subheader(txt["fcr_title"])
    col_fcr1, col_fcr2 = st.columns([2, 1])
    with col_fcr1:
        feed_in = st.number_input(txt["feed_cons"], value=10.0, key="dash_feed")
        avg_wt_input = st.number_input(txt["avg_wt"], value=0.5, key="dash_wt")
        fcr = feed_in / (active_birds * avg_wt_input) if (active_birds * avg_wt_input) > 0 else 0
    with col_fcr2:
        st.metric("FCR", f"{fcr:.2f}")

    st.divider()

    # ROI Section
    st.subheader(txt["roi_title"])
    with st.expander(txt["edit_fin"]):
        cx, cy = st.columns(2)
        c_cost = cx.number_input(txt["chick_cost"], value=1500)
        p_per_bird = cy.number_input(txt["mkt_price"], value=8500)
        # Using a dummy value for feed cost per kg since solver prices aren't global yet
        avg_feed_price = 1200 
        o_costs = st.number_input(txt["other_costs"], value=500)

    total_investment = (flock_size * c_cost) + (feed_in * avg_feed_price) + (active_birds * o_costs)
    expected_revenue = active_birds * p_per_bird
    net_profit = expected_revenue - total_investment
    roi_pct = (net_profit / total_investment * 100) if total_investment > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric(txt["invest"], f"{total_investment:,.0f} TSH")
    c2.metric(txt["revenue"], f"{expected_revenue:,.0f} TSH")
    if net_profit > 0:
        c3.metric(txt["profit"], f"{int(net_profit):,} TSH", f"{roi_pct:.1f}% ROI")
    else:
        c3.metric("Loss", f"{int(net_profit):,} TSH", f"{roi_pct:.1f}% ROI", delta_color="inverse")

    st.divider()

    # Vaccination Table
    vac_title = "💉 Ratiba ya Chanjo" if lang == "Kiswahili" else "💉 Vaccination Schedule"
    st.subheader(vac_title)
    h_day, h_vac, h_stat = "Day", "Vaccine", "Status"
    done_txt = "✅ Done" if lang == "English" else "✅ Imekamilika"
    pending_txt = "⏳ Pending" if lang == "English" else "⏳ Inasubiri"

    vac_data = {
        h_day: [1, 7, 14, 21, 28, 35],
        h_vac: ["Marek's/IB", "Gumboro 1", "Newcastle 1", "Gumboro 2", "Newcastle 2", "Fowl Pox"],
        h_stat: [done_txt if age_days >= d else pending_txt for d in [1, 7, 14, 21, 28, 35]]
    }
    st.table(pd.DataFrame(vac_data))

elif menu == txt["solver"]:
    st.title(txt["solve_title"])
    col_a, col_b = st.columns(2)
    with col_a:
        stage = st.selectbox(txt["stage"], list(STANDARDS.keys()))
        target_prot = STANDARDS[stage]
    with col_b:
        total_to_produce = st.number_input(txt["total"], min_value=1.0, value=100.0)
    
    use_premix = st.checkbox("Include 5% Premix", value=True)
    m_prot, s_prot = ING_DATABASE["Maize"]["prot"], ING_DATABASE["Soya Meal"]["prot"]
    
    if use_premix:
        usable_target = target_prot / 0.95 
        premix_kg = total_to_produce * 0.05
        remaining_kg = total_to_produce - premix_kg
    else:
        usable_target = target_prot
        premix_kg = 0
        remaining_kg = total_to_produce

    soya_ratio = (usable_target - m_prot) / (s_prot - m_prot)
    maize_kg, soya_kg = remaining_kg * (1 - soya_ratio), remaining_kg * soya_ratio

    st.subheader(f"📋 Recipe ({total_to_produce}kg)")
    recipe_df = pd.DataFrame({
        "Ingredient": ["Maize", "Soya Meal", "Premix"],
        "Weight (kg)": [f"{maize_kg:.2f}", f"{soya_kg:.2f}", f"{premix_kg:.2f}"]
    })
    st.table(recipe_df)

    with st.expander(txt["mixing"]):
        if lang == "Kiswahili":
            st.write("1. **Tabaka:** Tandaza mahindi kwanza, kisha soya juu yake.")
            st.write("2. **Mchanganyiko Mdogo:** Changanya Premix kwenye ndoo ndogo na 2kg za mahindi kwanza.")
            st.write("3. **Sheria ya Mihiko 3:** Geuza mchanganyiko mara 3.")
        else:
            st.write("1. **Layering:** Spread Maize first, then Soya on top.")
            st.write("2. **Pre-Mix:** Mix Premix with 2kg Maize in a bucket first.")
            st.write("3. **3-Shovel Rule:** Turn the pile 3 times.")

elif menu == txt["guide"]:
    st.title(txt["guide"])
    selected_ing = st.selectbox("Select Ingredient:", list(ING_DATABASE.keys()))
    data = ING_DATABASE[selected_ing]
    
    col_img, col_info = st.columns([1, 2])
    with col_img:
        raw_url = f"https://raw.githubusercontent.com/erickrugakingira-lab/feedconvo-app/main/assets/{data['img']}"
        st.image(raw_url, use_container_width=True)
    with col_info:
        st.subheader(f"🔍 {selected_ing} Quality Checks")
        for check in data["qc"]:
            if "✅" in check: st.success(check)
            else: st.error(check)

elif menu == txt["market"]:
    st.title(txt["market"])
    for name, info in ING_DATABASE.items():
        with st.container():
            c1, c2, c3 = st.columns([1, 2, 1])
            c1.markdown(f"### {name}")
            c2.write(f"**Price:** {info['price_per_kg']} TSH/kg")
            wa_link = f"https://wa.me/255700000000?text=I%20want%20to%20order%20{name}"
            c3.link_button(f"Order {name}", wa_link, type="primary")
            st.divider()

st.caption("🚀 Powered by FeedConvo Local Logistics")
