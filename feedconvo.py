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
        "img": "maize_grain.jpg", 
        "prot": 9.0, "en": 3350, 
        "details": "Primary energy source. High risk of Aflatoxins in humid areas.",
        "qc": [
            "✅ Moisture: Must be below 13% (grains should 'snap' when bitten).",
            "✅ Color: Uniform yellow; no black or greenish-blue dust (mold).",
            "✅ Smell: No musty or fermented odor.",
            "✅ Purity: No weevils or stones."
        ],
        "price_per_kg": 800
    },
    "Soya Meal": {
        "img": "soyameal.jpg",
        "prot": 44.0, "en": 2500, 
        "details": "High-quality vegetable protein. Requires proper toasting.",
        "qc": [
            "✅ Color: Light tan/golden. White is undercooked; dark brown is burnt.",
            "✅ Texture: Fine flakes; no large hard clumps.",
            "✅ Smell: Fresh, nutty aroma. No raw bean smell."
        ],
        "price_per_kg": 2200
    },
    "Fish Meal": {
        "img": "fishmeal.jpg",
        "prot": 55.0, "en": 2800, 
        "details": "Animal protein with essential amino acids.",
        "qc": [
            "✅ Salt: Should not be extremely salty to the taste.",
            "✅ Texture: No heavy grit or sand when rubbed.",
            "✅ Smell: Strong fishy smell is okay; 'rotten' is a fail."
        ],
        "price_per_kg": 3500
    },
    "Sunflower Cake": {
        "img": "sunflower_cake.jpeg",
        "prot": 24.0, "en": 2300, 
        "details": "Fiber source. Good for cost reduction in older birds.",
        "qc": [
            "✅ Fiber: No excessive black hulls (causes diarrhea).",
            "✅ Oil: Should not feel greasy or smell rancid.",
            "✅ Hardness: Should break easily by hand."
        ],
        "price_per_kg": 1100
    }
}

STANDARDS = {
    "Starter (Wk 1-2)": 22.0, 
    "Grower (Wk 3-4)": 20.0, 
    "Finisher (Wk 5+)": 18.0
}

# --- 3. CUSTOM STYLING (The Faded/Veiled Background Version) ---
bg_url = "https://raw.githubusercontent.com/erickrugakingira-lab/feedconvo-app/main/broiler_chicken.png"

st.markdown(f"""
    <style>
    /* 1. The Background with a White 'Veil' Overlay */
    .stApp {{
        background: linear-gradient(
            rgba(255, 255, 255, 0.70), 
            rgba(255, 255, 255, 0.70)
        ), 
        url("{bg_url}");
        background-attachment: fixed;
        background-size: contain; /* Keeps the zoom-out you liked */
        background-repeat: no-repeat;
        background-position: center bottom;
    }}

    /* 2. The Main Content Box - Solid White for Maximum Focus */
    .main {{ 
        background-color: #ffffff; /* Pure solid white */
        padding: 40px; 
        border-radius: 20px;
        box-shadow: 0 15px 50px rgba(0,0,0,0.1); /* Soft shadow to create depth */
        margin-top: 30px;
        border: 1px solid #e0e0e0;
    }}

    /* 3. Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: #e8f5e9; 
        border-right: 2px solid #c8e6c9;
    }}

    /* 4. Table and Text Styling for High Contrast */
    .stTable {{
        background-color: white;
        border-radius: 10px;
    }}
    
    h1, h2, h3 {{
        color: #1b5e20;
        text-shadow: none; /* Removes any glow that might make it blurry */
    }}
    </style>
    """, unsafe_allow_html=True)
    
# --- 4. SIDEBAR & LANGUAGE LOGIC ---
with st.sidebar:
    st.header("🚜 Farm Manager")
    
    # --- THE SWAHILI TOGGLE ---
    lang = st.radio("Chagua Lugha / Select Language:", ["English", "Kiswahili"])
    
    st.divider()
    
    # Text Dictionary for Translation
    t = {
       "English": {
            "dash": "📊 Dashboard", 
            "solver": "🧪 Feed Solver", 
            "guide": "📚 Guide", 
            "market": "🛒 Market",
            "birds": "Live Birds", 
            "age": "Age (Days)", 
            "yield": "Est. Yield (kg)",
            "fcr_title": "📈 FCR Tracker (Efficiency)", 
            "feed_cons": "Total Feed Consumed (kg)",
            "avg_wt": "Current Avg. Weight per Bird (kg)", 
            "roi_title": "💵 Profit & ROI Projection",
            "solve_title": "🧪 Precision Feed Solver",
            "stage": "Select Growth Stage:",
            "total": "Total Feed to Produce (kg)",
            "download": "📥 Download Recipe", 
            "mixing": "🥣 Mixing Instructions",
            "invest": "Total Investment", 
            "revenue": "Expected Revenue", 
            "profit": "Projected Profit",
            "edit_fin": "Adjust Costs & Prices", 
            "chick_cost": "Cost per Chick (TSH)",
            "mkt_price": "Market Price per KG (TSH)", 
            "other_costs": "Other Costs (Meds, Labor)"
        },
        "Kiswahili": {
            "dash": "📊 Dashibodi", 
            "solver": "🧪 Kikokotoo", 
            "guide": "📚 Mwongozo", 
            "market": "🛒 Soko",
            "birds": "Kuku Waliopo", 
            "age": "Umri (Siku)", 
            "yield": "Mavuno (kg)",
            "fcr_title": "📈 Ufanisi wa Chakula (FCR)", 
            "feed_cons": "Jumla ya Chakula (kg)",
            "avg_wt": "Wastani wa Uzito wa Kuku (kg)", 
            "roi_title": "💵 Makadirio ya Faida (ROI)",
            "solve_title": "🧪 Kikokotoo cha Chakula", # <--- THE MISSING KEY
            "stage": "Chagua Hatua ya Ukuaji:",
            "total": "Jumla ya Chakula (kg)",
            "download": "📥 Pakua Maelekezo", 
            "mixing": "🥣 Maelekezo ya Kuchanganya",
            "invest": "Jumla ya Gharama", 
            "revenue": "Mauzo Yanayotarajiwa", 
            "profit": "Faida Inayotarajiwa",
            "edit_fin": "Badili Gharama na Bei", 
            "chick_cost": "Gharama ya Kifaranga (TSH)",
            "mkt_price": "Bei ya Soko kwa KG (TSH)", 
            "other_costs": "Gharama Nyingine (Dawa, Mkaa)"
        }
    }

    # Current selection labels
    txt = t[lang]

    menu = st.radio("GO TO:", [txt["dash"], txt["solver"], txt["guide"], txt["market"]])
    
    st.divider()
    flock_size = st.number_input("Birds Started / Idadi ya Kuku", min_value=1, value=100)
    mortality = st.number_input("Mortality / Vifo", min_value=0, value=0)
    start_date = st.date_input("Hatch Date / Tarehe ya Kutolewa", datetime.date.today() - datetime.timedelta(days=14))

    active_birds = max(0, flock_size - mortality)
    age_days = (datetime.date.today() - start_date).days
    total_potential_yield = active_birds * 2.5 # Using 2.5kg as standard harvest weight

# --- 5. PAGE LOGIC ---

if menu == txt["dash"]:
    st.title(f"{txt['dash']}: Siku ya {age_days}")
    
    # Sehemu ya 1: Hali ya Kuku (Flock Metrics)
    m1, m2, m3 = st.columns(3)
    m1.metric(txt["birds"], f"{active_birds}", delta=f"-{mortality} vifo" if lang == "Kiswahili" else f"-{mortality} deaths", delta_color="inverse")
    m2.metric(txt["age"], f"{age_days}")
    m3.metric(txt["yield"], f"{total_potential_yield:.1f} kg")

    st.divider()

    # Sehemu ya 2: FCR (Efficiency)
    st.subheader(txt["fcr_title"])
    col_fcr1, col_fcr2 = st.columns([2, 1])
    with col_fcr1:
        feed_in = st.number_input(txt["feed_cons"], value=10.0)
        avg_wt_input = st.number_input(txt["avg_wt"], value=0.5)
        fcr = feed_in / (active_birds * avg_wt_input) if (active_birds * avg_wt_input) > 0 else 0
    with col_fcr2:
        st.metric("FCR", f"{fcr:.2f}")
        if fcr <= 1.6:
            st.success("Hongera! Ufanisi ni Mkubwa sana. ✅" if lang == "Kiswahili" else "Excellent Efficiency! ✅")
        elif fcr <= 1.9:
            st.warning("Wastani. Angalia upotevu wa chakula. ⚠️" if lang == "Kiswahili" else "Average. Watch for waste. ⚠️")
        else:
            st.error("Hatari! Angalia ubora wa chakula au magonjwa. 🚨" if lang == "Kiswahili" else "High FCR! Check feed/health. 🚨")

    st.divider()

    # Sehemu ya 3: ROI (Financials)
    st.subheader(txt["roi_title"])
    with st.expander(txt["edit_fin"]):
        cx, cy = st.columns(2)
        c_cost = cx.number_input(txt["chick_cost"], value=1500)
        m_price = cy.number_input(txt["mkt_price"], value=8500)
        o_costs = st.number_input(txt["other_costs"], value=50000)

    # Mahesabu ya Faida
    avg_feed_price = (ING_DATABASE["Maize"]["price_per_kg"] * 0.65) + (ING_DATABASE["Soya Meal"]["price_per_kg"] * 0.35)
    total_invest = (flock_size * c_cost) + (feed_in * avg_feed_price) + o_costs
    total_rev = total_potential_yield * m_price
    net_profit = total_rev - total_invest
    roi_pct = (net_profit / total_invest) * 100 if total_invest > 0 else 0

    r1, r2, r3 = st.columns(3)
    r1.metric(txt["invest"], f"{int(total_invest):,} TSH")
    r2.metric(txt["revenue"], f"{int(total_rev):,} TSH")
    
    if net_profit > 0:
        r3.metric(txt["profit"], f"{int(net_profit):,} TSH", f"{roi_pct:.1f}% ROI")
    else:
        r3.metric("Hasara Inayotarajiwa", f"{int(net_profit):,} TSH", f"{roi_pct:.1f}% ROI", delta_color="inverse")
        st.divider()

    # --- SECTION 4: VACCINATION (RESTORED & TRANSLATED) ---
    vac_title = "💉 Ratiba ya Chanjo" if lang == "Kiswahili" else "💉 Vaccination Schedule"
    st.subheader(vac_title)
    
    # Translation for Table Headers
    h_day = "Siku / Day" if lang == "Kiswahili" else "Day"
    h_vac = "Chanjo / Vaccine" if lang == "Kiswahili" else "Vaccine"
    h_stat = "Hali / Status" if lang == "Kiswahili" else "Status"

    # Vaccination Logic based on age_days
    done_txt = "✅ Imekamilika" if lang == "Kiswahili" else "✅ Done"
    pending_txt = "⏳ Inasubiri" if lang == "Kiswahili" else "⏳ Pending"

    vac_data = {
        h_day: [1, 7, 14, 21, 28, 35],
        h_vac: [
            "Marek's/IB", 
            "Gumboro 1", 
            "Newcastle 1", 
            "Gumboro 2", 
            "Newcastle 2", 
            "Fowl Pox"
        ],
        h_stat: ["✅ Done" if age_days >= d else "⏳ Pending" for d in [1, 7, 14, 21, 28, 35]]
    }
    
    # Applying the localized status text
    vac_data[h_stat] = [done_txt if age_days >= d else pending_txt for d in [1, 7, 14, 21, 28, 35]]
    
    st.table(pd.DataFrame(vac_data))

    # Warning for upcoming vaccines
    upcoming = [d for d in [1, 7, 14, 21, 28, 35] if d > age_days]
    if upcoming:
        next_v = upcoming[0]
        days_left = next_v - age_days
        msg = f"⚠️ Chanjo inayofuata ni baada ya siku {days_left}" if lang == "Kiswahili" else f"⚠️ Next vaccine is in {days_left} days"
        st.info(msg)
        
elif menu == txt["solver"]:
    st.title(txt["solve_title"])
    
    col_a, col_b = st.columns(2)
    with col_a:
        stage = st.selectbox(txt["stage"], list(STANDARDS.keys()))
        target_prot = STANDARDS[stage]
    with col_b:
        total_to_produce = st.number_input(txt["total"], min_value=1.0, value=100.0)
    
    # --- THE PREMIX BUTTON (RESTORED) ---
    premix_label = "Weka Virutubisho 5% (Inashauriwa)" if lang == "Kiswahili" else "Include 5% Premix/Minerals (Recommended)"
    use_premix = st.checkbox(premix_label, value=True)
    
    # --- CALCULATION LOGIC ---
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

    # --- DISPLAY TABLE ---
    st.subheader(f"📋 {txt['download']} ({total_to_produce}kg)")
    
    # Localized Table Headers
    header_ing = "Kiungo / Ingredient" if lang == "Kiswahili" else "Ingredient"
    header_wt = "Uzito / Weight (kg)" if lang == "Kiswahili" else "Weight (kg)"
    
    recipe_df = pd.DataFrame({
        header_ing: ["Mahindi / Maize", "Soya / Soya Meal", "Virutubisho / Premix"],
        header_wt: [f"{maize_kg:.2f} kg", f"{soya_kg:.2f} kg", f"{premix_kg:.2f} kg"]
    })
    st.table(recipe_df)

    # --- THE DOWNLOAD BUTTON (RESTORED & TRANSLATED) ---
    # Creating the translated text file content
    if lang == "Kiswahili":
        recipe_text = f"""
        MCHANGANYIKO WA CHAKULA CHA KUKU (FEEDCONVO)
        ------------------------------------------
        Tarehe: {datetime.date.today()}
        Hatua: {stage}
        Jumla: {total_to_produce} kg
        
        MAHITAJI:
        1. Mahindi: {maize_kg:.2f} kg
        2. Soya: {soya_kg:.2f} kg
        3. Premix: {premix_kg:.2f} kg
        
        MAELEKEZO YA KUCHANGANYA:
        - Tandaza Mahindi kwanza, kisha Soya juu yake.
        - Changanya Premix na 2kg za Mahindi kwanza kwenye ndoo.
        - Geuza mchanganyiko wote mara 3 kwa jembe/mwiko.
        ------------------------------------------
        Imetengenezwa na App ya FeedConvo
        """
    else:
        recipe_text = f"Date: {datetime.date.today()}\nStage: {stage}\nMaize: {maize_kg:.2f}kg\nSoya: {soya_kg:.2f}kg\nPremix: {premix_kg:.2f}kg"

    st.download_button(
        label=txt["download"],
        data=recipe_text,
        file_name=f"recipe_{stage}_{lang}.txt",
        mime="text/plain",
    )

    # --- MIXING INSTRUCTIONS (RESTORED) ---
    with st.expander(txt["mixing"]):
        if lang == "Kiswahili":
            st.write("1. **Tabaka:** Tandaza mahindi kwanza, kisha soya juu yake.")
            st.write("2. **Mchanganyiko Mdogo:** Changanya Premix kwenye ndoo ndogo na 2kg za mahindi kwanza kuzuia mabonge.")
            st.write("3. **Sheria ya Mihiko 3:** Geuza mchanganyiko mara 3 hadi rangi iwe moja nchi nzima.")
        else:
            st.write("1. **Layering:** Spread Maize first, then Soya on top.")
            st.write("2. **Pre-Mix:** Mix your Premix in a small bucket with 2kg of Maize before adding to the big pile.")
            st.write("3. **The 3-Shovel Rule:** Turn the pile at least 3 times until uniform.")
            
elif menu == "📚 Ingredient Guide":
    st.title("📚 Quality Control Guide")
    for name, info in ING_DATABASE.items():
        with st.expander(f"🔍 Inspecting {name}"):
            c1, c2 = st.columns([1, 2])
            with c1:
                if os.path.exists(info["img"]): st.image(info["img"])
                else: st.warning("Photo missing on GitHub")
            with c2:
                for check in info["qc"]: st.write(check)

elif menu == "🛒 Marketplace":
    st.title("🛒 Supplier Marketplace")
    cols = st.columns(2)
    for i, (name, info) in enumerate(ING_DATABASE.items()):
        with cols[i % 2]:
            st.markdown(f"""
            <div style="border:1px solid #ddd; padding:15px; border-radius:10px; margin-bottom:10px; background:white;">
                <h4>{name}</h4>
                <p>Price: <b>{info['price_per_kg']} TSH/kg</b></p>
                <a href="https://wa.me/255700000000" target="_blank"><button style="width:100%; background:#1b4332; color:white; border:none; padding:8px; border-radius:5px; cursor:pointer;">Order Now</button></a>
            </div>
            """, unsafe_allow_html=True)
