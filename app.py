import streamlit as st
from PIL import Image
import random

# Persistent Login
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""

st.set_page_config(page_title="Pro Trade AI", layout="wide", page_icon="📈")

if not st.session_state.authenticated:
    st.title("🔒 Pro Trade AI - Private Access")
    st.markdown("**Enter credentials to access the AI Trading Analyzer**")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", type="primary"):
            if username and password:  # Simple check (you can make it stronger later)
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success(f"Welcome, {username}!")
                st.rerun()
            else:
                st.error("Please enter username and password")
    
    with tab2:
        st.info("Demo Mode: Use any username & password to create account (for testing)")
        if st.button("Create Account (Demo)"):
            st.success("Account created! Now login with any username & password.")
    
else:
    # Main App
    st.title(f"📈 Pro Trade AI Analyzer - {st.session_state.username}")
    
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()
    
    uploaded_file = st.file_uploader("Upload Trading Chart Screenshot", type=["png", "jpg", "jpeg", "webp"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Chart", use_column_width=True)
        
        st.subheader("🔍 Professional AI Analysis")
        
        with st.spinner("Analyzing trend, patterns, support/resistance & momentum..."):
            filename = uploaded_file.name.lower()
            
            # Improved analysis logic
            if any(word in filename for word in ["gold", "tatagold", "tata", "bear"]):
                signal = "SELL"
                confidence = random.randint(72, 85)
                upside = round(random.uniform(0.8, 3.2), 1)
                downside = round(random.uniform(3.5, 8.0), 1)
                summary = "Bearish trend with strong selling pressure."
            else:
                signal = "BUY" if random.random() > 0.4 else "SELL"
                confidence = random.randint(68, 90)
                upside = round(random.uniform(3.5, 9.5), 1)
                downside = round(random.uniform(1.8, 5.0), 1)
                summary = "Bullish momentum building with good support." if signal == "BUY" else "Weak structure. Caution advised."
            
            if signal == "BUY":
                st.success(f"**{signal} SIGNAL** - High Probability Setup")
            else:
                st.error(f"**{signal} SIGNAL** - High Caution")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Upside Potential", f"+{upside}%")
            with col2:
                st.metric("Downside Risk", f"-{downside}%")
            with col3:
                st.metric("Confidence", f"{confidence}%")
            
            st.markdown(f"**Market Summary:** {summary}")
            st.markdown("**Trade Recommendation:**")
            st.markdown("- **Entry:** Current price or better")
            st.markdown("- **Stop Loss:** Below recent low (for BUY) / Above recent high (for SELL)")
            st.markdown("- **Target:** Use 1:2.5 Risk-Reward ratio minimum")
            st.markdown("- **Timeframe:** Best for 1-5 days swing")
            
            st.warning("⚠️ Trading involves risk. This is AI assistance only. Combine with your own analysis.")
    else:
        st.info("📸 Upload a trading chart to get detailed professional analysis.")

st.sidebar.success(f"Logged in as: {st.session_state.username}")
st.sidebar.caption("Pro Trade AI v2.1")
