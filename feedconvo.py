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

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("🚜 Farm Manager")
    menu = st.radio("GO TO:", ["📊 Dashboard", "🧪 Feed Solver", "📚 Ingredient Guide", "🛒 Marketplace"])
    st.divider()
    flock_size = st.number_input("Birds", value=100)
    start_date = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=7))

# Calculations
age_days = (datetime.date.today() - start_date).days
current_stage = "Starter (Wk 1)" if age_days < 8 else ("Grower (Wk 2-3)" if age_days < 22 else "Finisher (Wk 4+)")

# --- 6. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title(f"📊 Flock Performance: Day {age_days}")
    
    # 1. CORE CALCULATIONS
    # Get target weight in grams (g) based on age
    weights_g = [42, 185, 450, 910, 1450, 1980, 2400]
    target_weight_g = weights_g[min(age_days//7, 6)]
    expected_yield_kg = (active_birds * target_weight_g) / 1000

    # 2. TOP METRICS
    c1, c2, c3 = st.columns(3)
    c1.metric("Live Birds", f"{active_birds}")
    c2.metric("Mortality Rate", f"{(mortality/flock_size)*100:.1f}%", delta_color="inverse")
    c3.metric("Expected Yield", f"{expected_yield_kg:.1f} kg")

    st.divider()

    # 3. ROI CALCULATOR SECTION
    st.subheader("💰 ROI & Profit Calculator")
    with st.expander("Click to Edit Costs & Prices"):
        col_a, col_b = st.columns(2)
        chick_cost = col_a.number_input("Cost per Day-Old Chick (TSH)", value=1800)
        sale_price_kg = col_b.number_input("Selling Price (TSH per kg)", value=8500)
        other_costs = st.number_input("Other Costs (Medication, Heat, Water) per Bird", value=500)

    # Calculate Total Expenses
    total_chick_investment = flock_size * chick_cost
    total_other_expenses = active_birds * other_costs
    # Assuming average feed consumption to date
    estimated_feed_cost = (active_birds * (age_days * 0.1) * 1200) # Placeholder estimate
    total_investment = total_chick_investment + total_other_expenses + estimated_feed_cost
    
    # Calculate Potential Revenue
    potential_revenue = expected_yield_kg * sale_price_kg
    profit = potential_revenue - total_investment
    roi_percent = (profit / total_investment) * 100 if total_investment > 0 else 0

    # Display ROI Cards
    r1, r2, r3 = st.columns(3)
    r1.metric("Total Investment", f"{int(total_investment):,} TSH")
    r2.metric("Potential Revenue", f"{int(potential_revenue):,} TSH")
    
    # Color coding profit (Green for +, Red for -)
    if profit > 0:
        r3.metric("Estimated Profit", f"{int(profit):,} TSH", f"{roi_percent:.1f}% ROI")
    else:
        r3.metric("Estimated Profit", f"{int(profit):,} TSH", f"{roi_percent:.1f}% ROI", delta_color="inverse")

    st.divider()

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
