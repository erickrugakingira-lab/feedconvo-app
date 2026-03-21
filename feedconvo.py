import streamlit as st
import pulp
import pandas as pd
import datetime
import plotly.express as px
import base64
import urllib.parse
import os

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="FeedConvo: QC & Solver", layout="wide", page_icon="🛡️")

# --- 2. IMAGE LOADER ---
def get_base64_image(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

bg_data = get_base64_image("broiler chicken.png")
bg_style = f"url('data:image/png;base64,{bg_data}')" if bg_data else "none"

# --- 3. STYLING (Visibility & QC Cards) ---
st.markdown(f"""
<style>
    .stApp {{
        background: linear-gradient(rgba(255,255,255,0.75), rgba(255,255,255,0.75)), {bg_style};
        background-size: cover; background-attachment: fixed;
    }}
    
    /* Sidebar Text Visibility */
    section[data-testid="stSidebar"] {{ background-color: rgba(27, 67, 50, 0.95) !important; }}
    section[data-testid="stSidebar"] .stMarkdown h2, 
    section[data-testid="stSidebar"] label {{ color: white !important; font-weight: bold; }}

    /* CRITICAL: Fix for Invisible Input Text */
    input {{ 
        color: #000000 !important; 
        background-color: #FFFFFF !important; 
    }}
    
    /* Ensuring the box itself is visible with a border */
    div[data-baseweb="input"] {{ 
        background-color: #FFFFFF !important; 
        border: 2px solid #1b4332 !important; 
        border-radius: 8px; 
    }}
</style>
""", unsafe_allow_html=True)

# --- 4. DATA & QC CHECKLISTS ---
ING_DATABASE = {
    "Maize": {
        "file": "maize grain.jpg", "prot": 9.0, "en": 3350,
        "details": "Energy source. High risk of Aflatoxins.",
        "qc": ["Moisture < 13% (Grain cracks when bitten)", "No visible green/black mold", "No musty or fermented smell", "No insect/weevil damage"],
        "link": "https://wa.me/255XXXXXXXXX"
    },
    "Soya Meal": {
        "file": "soyameal.jpg", "prot": 44.0, "en": 2500,
        "details": "Main protein. Check toasting quality.",
        "qc": ["Color is light tan/gold (not white/raw)", "Nutty aroma (not beany/raw)", "Texture is flaky, not clumped/damp"],
        "link": "https://wa.me/255XXXXXXXXX"
    },
    "Fish Meal": {
        "file": "fishmeal.jpg", "prot": 55.0, "en": 2800,
        "details": "Animal protein. Check salt and freshness.",
        "qc": ["Low salt content (not crusty)", "No 'rotten' or overly 'oily' smell", "Free from sand/grit contamination"],
        "link": "https://wa.me/255XXXXXXXXX"
    },
    "Sunflower Cake": {
        "file": "sunflower.jpg", "prot": 24.0, "en": 2300,
        "details": "Fiber source. Watch for excessive hulls.",
        "qc": ["Minimal black hulls (too much fiber is bad)", "No dampness or caking", "Consistent brown color"],
        "link": "https://wa.me/255XXXXXXXXX"
    }
}

STANDARDS = {"Starter (Wk 1)": 22.5, "Grower (Wk 2-3)": 20.0, "Finisher (Wk 4+)": 18.5}

# --- 5. SIDEBAR & LOGIC ---
with st.sidebar:
    st.header("🚜 Farm Manager")
    
    # User inputs
    flock_size = st.number_input("Total Birds Started", min_value=1, value=100)
    mortality = st.number_input("Mortality (Dead Birds)", min_value=0, value=0)
    
    # NEW: Manual Harvest Target
    harvest_target = st.number_input("Target Weight at Harvest (kg)", min_value=0.1, value=2.5, step=0.1)
    
    start_date = st.date_input("Hatch Date", datetime.date.today() - datetime.timedelta(days=7))
    
    st.divider()
    menu = st.radio("GO TO:", ["📊 Dashboard", "🧪 Feed Solver", "📚 Ingredient Guide", "🛒 Marketplace"])
    
    # Calculations (Calculated AFTER inputs)
    active_birds = flock_size - mortality
    age_days = (datetime.date.today() - start_date).days
    
    # Current standard weight for the graph/metrics
    weights_g = [42, 185, 450, 910, 1450, 1980, 2400]
    index = min(max(age_days // 7, 0), 6)
    current_std_weight_kg = weights_g[index] / 1000
    
    # Harvest Projection Logic
    total_harvest_yield_kg = active_birds * harvest_target

# --- 6. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title(f"📊 Performance & Projections: Day {age_days}")
    
    # 1. METRICS ROW
    c1, c2, c3 = st.columns(3)
    c1.metric("Live Birds", f"{active_birds}")
    
    # Current weight estimation based on standard growth
    current_meat_kg = active_birds * current_std_weight_kg
    c2.metric("Current Meat (est.)", f"{current_meat_kg:.1f} kg")
    
    # Harvest target from your sidebar input
    c3.metric("Projected Harvest", f"{total_harvest_yield_kg:.1f} kg")

    st.divider()

    # 2. ROI CALCULATOR
    st.subheader("💰 Profit & Loss Projection (At Harvest)")
    with st.expander("📝 Edit Costs & Market Prices"):
        col_a, col_b = st.columns(2)
        chick_cost = col_a.number_input("Cost per Chick (TSH)", value=1800)
        sale_price_kg = col_b.number_input("Selling Price per KG (TSH)", value=8500)
        fixed_costs = st.number_input("Other costs (Medication/Heat) per bird", value=500)

    # UPDATED REVENUE CALCULATION:
    # We use 'total_harvest_yield_kg' which we defined in the Sidebar logic
    total_investment = (flock_size * chick_cost) + (active_birds * fixed_costs)
    potential_revenue = total_harvest_yield_kg * sale_price_kg
    net_profit = potential_revenue - total_investment
    roi_pct = (net_profit / total_investment * 100) if total_investment > 0 else 0

    # 3. DISPLAY ROI CARDS
    r1, r2, r3 = st.columns(3)
    st.write(f"**Total Investment:** {int(total_investment):,} TSH")
    st.write(f"**Est. Revenue at Harvest:** {int(potential_revenue):,} TSH")
    
    if net_profit > 0:
        st.success(f"**Projected Profit:** {int(net_profit):,} TSH ({roi_pct:.1f}% ROI)")
    else:
        st.error(f"**Projected Loss:** {int(net_profit):,} TSH ({roi_pct:.1f}%)")
    # --- ADD THIS INSIDE THE DASHBOARD BLOCK ---
st.divider()
st.subheader("💉 Vaccination & Health Schedule")

# 1. Define the Schedule Data
vaccine_data = {
    "Day": [1, 7, 14, 21, 28],
    "Vaccine": ["Marek's / IB / Newcastle", "Gumboro (1st Dose)", "Newcastle (Lasota)", "Gumboro (2nd Dose)", "Newcastle (Booster)"],
    "Method": ["Hatchery Spray/Injection", "Drinking Water", "Drinking Water/Eye Drop", "Drinking Water", "Drinking Water"],
    "Status": ["✅ Completed" if age_days >= d else "⏳ Pending" for d in [1, 7, 14, 21, 28]]
}
df_vac = pd.DataFrame(vaccine_data)

# 2. Display as an Interactive Table
with st.expander("📅 View Full Schedule for this Flock"):
    st.table(df_vac)
    st.caption("⚠️ Note: Always consult a local vet. Ensure birds are healthy before vaccinating.")

# 3. Smart Alert: Tells the farmer what is due TODAY
due_today = df_vac[df_vac['Day'] == (age_days if age_days in [1,7,14,21,28] else None)]
if not due_today.empty:
    st.error(f"🚨 **ACTION REQUIRED:** Today is Day {age_days}. Vaccine due: {due_today['Vaccine'].values[0]}")
else:
    st.success("✅ No vaccines scheduled for today.")
   
    # RESTORE GRAPH
    st.subheader("📈 Growth Curve")
    df_growth = pd.DataFrame({"Day": [0,7,14,21,28,35,42], "Target (g)": weights_g})
    fig = px.line(df_growth, x="Day", y="Target (g)", markers=True)
    fig.update_traces(line_color='#1b4332')
    st.plotly_chart(fig, use_container_width=True)
    # 4. RESTORE THE GROWTH GRAPH
    st.subheader("📈 Growth Projection")
    df_growth = pd.DataFrame({
        "Day": [0, 7, 14, 21, 28, 35, 42],
        "Target (g)": weights_g
    })
    fig = px.line(df_growth, x="Day", y="Target (g)", markers=True, title="Standard Broiler Growth Curve")
    fig.update_traces(line_color='#1b4332', line_width=3)
    st.plotly_chart(fig, use_container_width=True)
    
 # --- 7. INGREDIENT GUIDE BLOCK ---
elif menu == "📚 Ingredient Guide":
    st.title("📚 Ingredient Knowledge & QC")
    st.write("Click an ingredient to learn about nutrition, safety, and quality control.")
    
    # 1. Selection Dropdown
    sel_ing = st.selectbox("Select Ingredient to Inspect:", list(ING_DATABASE.keys()))
    ing_data = ING_DATABASE[sel_ing]
    
    col1, col2 = st.columns([1, 1.5])
    
    # 2. Display Local Image
    with col1:
        img_b64_ing = get_base64_image(ing_data['file'])
        if img_b64_ing:
            st.markdown(f'''
                <div style="border: 2px solid #1b4332; border-radius: 15px; overflow: hidden;">
                    <img src="data:image/jpg;base64,{img_b64_ing}" style="width:100%; display:block;">
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ Image not found: Please upload '{ing_data['file']}' to GitHub.")
    
    # 3. QC Checklist & Nutrition
    with col2:
        st.subheader(f"🔍 {sel_ing} Quality Inspection")
        st.info(f"**Nutrition:** {ing_data['prot']}% Protein | {ing_data['en']} kcal/kg")
        
        st.write("📈 **Checklist for Farmers:** (Check these before mixing)")
        # This creates the interactive checklist
        for point in ing_data['qc']:
            st.checkbox(point, key=f"qc_check_{sel_ing}_{point}")
            
        st.markdown(f"""
            <div style="background-color: #fff3cd; padding: 15px; border-radius: 10px; border-left: 5px solid #ffc107; color: #856404;">
                <strong>💡 Management Tip:</strong> {ing_data['details']}
            </div>
        """, unsafe_allow_html=True)
    
# --- 8. FEED SOLVER ---
elif menu == "🧪 Feed Solver":
    st.title("Least-Cost Solver")
    avail = st.multiselect("Active Ingredients:", list(ING_DATABASE.keys()), default=["Maize", "Soya Meal"])
    prices = {i: st.number_input(f"{i} (TSH/kg)", value=850 if i=="Maize" else 2600) for i in avail}
    
    if st.button("Solve Formula"):
        prob = pulp.LpProblem("Feed", pulp.LpMinimize)
        vars = pulp.LpVariable.dicts("KG", avail, lowBound=0)
        prob += pulp.lpSum([vars[i] * prices[i] for i in avail])
        prob += pulp.lpSum([vars[i] for i in avail]) == 100
        prob += pulp.lpSum([vars[i] * ING_DATABASE[i]["prot"] for i in avail]) >= STANDARDS[current_stage] * 100
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        if pulp.LpStatus[prob.status] == 'Optimal':
            recipe = f"FeedConvo Recipe ({current_stage}):\n"
            for i in avail:
                if vars[i].varValue > 0:
                    st.success(f"**{i}**: {vars[i].varValue:.2f} kg")
                    recipe += f"- {i}: {vars[i].varValue:.2f} kg\n"
            st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(recipe)}" class="share-btn">📲 Share Recipe on WhatsApp</a>', unsafe_allow_html=True)

# --- 9. MARKETPLACE ---
elif menu == "🛒 Marketplace":
    st.title("Verified Suppliers")
    cols = st.columns(3)
    for idx, (name, meta) in enumerate(ING_DATABASE.items()):
        with cols[idx % 3]:
            img_b64 = get_base64_image(meta['file'])
            img_tag = f'<img src="data:image/jpg;base64,{img_b64}" style="width:100%; height:120px; object-fit:cover; border-radius:8px;">' if img_b64 else ""
            st.markdown(f'<div class="market-card">{img_tag}<h3>{name}</h3><a href="{meta["link"]}" class="buy-btn">Order</a></div>', unsafe_allow_html=True)
