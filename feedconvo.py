import streamlit as st
import pulp
import pandas as pd
import datetime
import base64
import urllib.parse

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="FeedConvo: Safety First", layout="wide", page_icon="🌽")

# --- 2. THE BACKGROUND IMAGE ---
IMG_FILENAME = "broiler chicken.png"
def get_base64_image(file):
    try:
        with open(file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except: return None

img_data = get_base64_image(IMG_FILENAME)
bg_style = f"url('data:image/png;base64,{img_data}')" if img_data else "none"

# --- 3. STYLING ---
st.markdown(f"""
<style>
    .stApp {{
        background: linear-gradient(rgba(255,255,255,0.88), rgba(255,255,255,0.88)), {bg_style};
        background-size: cover; background-attachment: fixed;
    }}
    section[data-testid="stSidebar"] {{ background-color: rgba(27, 67, 50, 0.95) !important; }}
    section[data-testid="stSidebar"] * {{ color: white !important; }}
    input {{ color: black !important; background-color: white !important; }}
    
    .market-card {{
        background: white !important; border-radius: 15px; padding: 15px; 
        border: 1px solid #eee; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }}
    .ing-img {{ width: 100%; height: 150px; object-fit: cover; border-radius: 10px; }}
    .buy-btn {{
        display: block; padding: 10px; background-color: #f2a900;
        color: #1b4332 !important; text-decoration: none; border-radius: 8px; 
        font-weight: bold; margin-top: 10px;
    }}
</style>
""", unsafe_allow_html=True)

# --- 4. ENHANCED INGREDIENT DATA ---
# Replace the image URLs below with your own or use these high-quality placeholders
ING_DATABASE = {
    "Maize": {
        "img": "https://share.google/p71wOG9Dq0O0lSUj7",
        "prot": 9.0, "en": 3350,
        "details": "Maize is the primary energy source. **Aflatoxin Alert:** Never use maize that looks greenish/black or smells musty. Keep moisture below 13%. Use toxin binders if quality is doubtful.",
        "link": "https://wa.me/255659748732"
    },
    "Soya Meal": {
        "img": "https://share.google/56NKScgAXzyIJqZl6",
        "prot": 44.0, "en": 2500,
        "details": "Soya is the main protein builder. Ensure it is well-toasted to remove anti-nutritional factors. It should be light brown and nutty in smell.",
        "link": "https://wa.me/255XXXXXXXXX"
    },
    "Fish Meal": {
        "img": "https://share.google/ugs43auRrCLlJCtpO",
        "prot": 55.0, "en": 2800,
        "details": "High in amino acids. **Safety:** Ensure it is salt-free and not rancid. Rancid fish meal causes 'black vomit' in chicks.",
        "link": "https://wa.me/255XXXXXXXXX"
    }
}

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("🚜 Farm Manager")
    menu = st.radio("MENU", ["📊 Dashboard", "🧪 Feed Solver", "📚 Ingredient Guide", "🛒 Marketplace"])
    st.divider()
    flock_size = st.number_input("Flock Size", value=100)

# --- 6. NEW FEATURE: INGREDIENT GUIDE ---
if menu == "📚 Ingredient Guide":
    st.title("Poultry Ingredient Library")
    st.write("Click an ingredient to learn about nutrition and safety.")
    
    selected_ing = st.selectbox("Select Ingredient to Study:", list(ING_DATABASE.keys()))
    data = ING_DATABASE[selected_ing]
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(data['img'], use_container_width=True)
    with col2:
        st.subheader(f"Nutrition: {selected_ing}")
        st.write(f"**Protein:** {data['prot']}% | **Energy:** {data['en']} kcal/kg")
        st.warning(data['details'])

# --- 7. UPDATED FEED SOLVER ---
elif menu == "🧪 Feed Solver":
    st.title("Smart Solver")
    avail = st.multiselect("Choose Ingredients:", list(ING_DATABASE.keys()), default=["Maize", "Soya Meal"])
    
    # Simple solve logic (abbreviated for clarity)
    if st.button("Calculate Mix"):
        st.success("Balanced Recipe Found!")
        for i in avail:
            with st.expander(f"👁️ View {i} Quality Tips"):
                st.write(ING_DATABASE[i]['details'])
            st.write(f"**{i}**: 60.50 kg") # Example placeholder

# --- 8. MARKETPLACE WITH REAL IMAGES ---
elif menu == "🛒 Marketplace":
    st.title("Ingredient Marketplace")
    cols = st.columns(3)
    for idx, (name, meta) in enumerate(ING_DATABASE.items()):
        with cols[idx % 3]:
            st.markdown(f"""
            <div class="market-card">
                <img src="{meta['img']}" class="ing-img">
                <h3>{name}</h3>
                <p>{meta['prot']}% Protein</p>
                <a href="{meta['link']}" target="_blank" class="buy-btn">Order Now</a>
            </div>
            """, unsafe_allow_html=True)
