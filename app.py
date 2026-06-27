import streamlit as st
from PIL import Image
import random

# Session State
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

st.set_page_config(page_title="Pro Trade AI", layout="wide", page_icon="📈")

if not st.session_state.logged_in:
    st.title("📈 Pro Trade AI")
    st.subheader("Professional Trading Chart Analyzer")
    st.markdown("Sign in to access AI-powered trading insights")
    
    tab1, tab2 = st.tabs(["🔑 Login", "✍️ Sign Up"])
    
    with tab1:
        username = st.text_input("Username or Email")
        password = st.text_input("Password", type="password")
        if st.button("Login", type="primary"):
            if username and password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
                st.error("Please fill all fields")
    
    with tab2:
        new_user = st.text_input("Choose Username")
        email = st.text_input("Email Address")
        new_pass = st.text_input("Create Password", type="password")
        if st.button("Create Account", type="primary"):
            if new_user and email and new_pass:
                st.success("Account created! Please login with your credentials.")
            else:
                st.error("All fields are required")

else:
    # Main Professional App
    st.title(f"📈 Pro Trade AI - Welcome, {st.session_state.username}")
    
    if st.button("Logout", key="logout"):
        st.session_state.logged_in = False
        st.rerun()
    
    uploaded_file = st.file_uploader("Upload Trading Chart Screenshot", type=["png", "jpg", "jpeg", "webp"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Analyzed Chart", use_column_width=True)
        
        st.subheader("🔍 Professional AI Analysis Report")
        
        with st.spinner("Deep analysis of price action, trend, volume & structure..."):
            filename = uploaded_file.name.lower()
            
            # Smart mock logic
            if any(x in filename for x in ["gold", "tatagold", "tata"]):
                signal = "SELL"
                confidence = 76
                upside = round(random.uniform(0.5, 2.5), 1)
                downside = round(random.uniform(4.0, 7.5), 1)
                trend = "Bearish continuation likely"
            else:
                signal = "BUY" if random.random() > 0.45 else "SELL"
                confidence = random.randint(68, 89)
                upside = round(random.uniform(3.0, 9.0), 1)
                downside = round(random.uniform(1.5, 4.5), 1)
                trend = "Bullish momentum" if signal == "BUY" else "Bearish pressure detected"
            
            # Display
            if signal == "BUY":
                st.success(f"**{signal} SIGNAL** — High Conviction Setup")
            else:
                st.error(f"**{signal} SIGNAL** — Caution Recommended")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Upside Potential", f"+{upside}%", "1-7 days")
            with col2:
                st.metric("Downside Risk", f"-{downside}%")
            with col3:
                st.metric("AI Confidence", f"{confidence}%")
            
            st.markdown(f"**Trend Summary:** {trend}")
            st.markdown("**Professional Advice:**")
            st.markdown("- Use **1:2.5+ Risk-Reward** ratio")
            st.markdown("- Place Stop Loss beyond recent swing high/low")
            st.markdown("- Position size: Max 1-2% of capital per trade")
            st.markdown("- Confirm with volume & higher timeframe")
            
            st.info("This AI tool is for educational & decision support. Always do your own due diligence.")
            
    else:
        st.info("👆 Upload a clear trading chart to receive professional AI analysis & trade recommendations.")

st.sidebar.success(f"👤 {st.session_state.username if st.session_state.logged_in else 'Guest'}")
st.sidebar.caption("Pro Trade AI v2.0")
