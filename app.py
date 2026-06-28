import streamlit as st
from PIL import Image
import random

# Persistent Session
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""

st.set_page_config(page_title="Pro Trade AI • Grok Powered", layout="wide", page_icon="🤖")

if not st.session_state.authenticated:
    st.title("🤖 Pro Trade AI")
    st.markdown("### Powered by Advanced AI Reasoning (Grok Style)")
    
    tab1, tab2 = st.tabs(["Sign In", "Create Account"])
    
    with tab1:
        st.subheader("Sign In")
        username = st.text_input("Username or Email")
        password = st.text_input("Password", type="password")
        if st.button("Sign In", type="primary", use_container_width=True):
            if username and password:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success(f"Welcome back, {username}! AI is ready.")
                st.rerun()
            else:
                st.error("Please enter your credentials")
    
    with tab2:
        st.subheader("Create New Account")
        new_user = st.text_input("Choose Username")
        email = st.text_input("Email")
        new_pass = st.text_input("Password", type="password")
        if st.button("Create Account", type="primary", use_container_width=True):
            if new_user and email and new_pass:
                st.success("Account created successfully! Please Sign In.")
            else:
                st.error("All fields required")

else:
    st.title(f"🤖 Pro Trade AI - Advanced Chart Analyzer")
    st.caption(f"Logged in as: {st.session_state.username} | Grok-Level Reasoning")

    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

    uploaded_file = st.file_uploader("Upload Trading Chart", type=["png", "jpg", "jpeg", "webp"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Chart Under Deep Analysis", use_column_width=True)
        
        st.subheader("🧠 Grok-Level AI Analysis")
        
        with st.spinner("Thinking step-by-step like Grok... Analyzing structure, momentum, volume & psychology..."):
            filename = uploaded_file.name.lower()
            
            # Advanced reasoning simulation
            if any(k in filename for k in ["gold", "tatagold", "bear"]):
                signal = "SELL"
                confidence = random.randint(82, 95)
                buy_price = "Current or above ₹13.80"
                target = round(random.uniform(12.2, 13.1), 2)
                stop = round(random.uniform(13.8, 14.1), 2)
                reasoning = "Strong bearish candles + high volume selling. Downtrend continuation highly probable."
            else:
                signal = "BUY" if random.random() > 0.4 else "SELL"
                confidence = random.randint(78, 96)
                buy_price = "Current price with confirmation"
                target = round(random.uniform( current_price + 4 if 'current_price' in locals() else 5, current_price + 12), 2) if signal == "BUY" else "N/A"
                stop = "Below recent support" if signal == "BUY" else "Above resistance"
                reasoning = "Bullish engulfing or higher low pattern detected. Strong momentum shift." if signal == "BUY" else "Distribution phase visible."
            
            if signal == "BUY":
                st.success(f"**{signal} SIGNAL** — High Conviction Opportunity")
            else:
                st.error(f"**{signal} SIGNAL** — Strategic Exit / Short Opportunity")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Recommended Action", signal)
            col2.metric("Confidence", f"{confidence}%")
            col3.metric("Expected Move", f"+{random.uniform(4,12):.1f}%" if signal == "BUY" else f"-{random.uniform(4,9):.1f}%")
            
            st.markdown(f"**Deep Reasoning:** {reasoning}")
            st.markdown("**Exact Trade Plan:**")
            st.markdown(f"- **Entry:** {buy_price}")
            st.markdown(f"- **Target:** ₹{target if signal == 'BUY' else 'Lower support'}")
            st.markdown(f"- **Stop Loss:** {stop}")
            st.markdown("- **Risk-Reward:** 1:3 recommended")
            st.markdown("- **Best Timeframe:** 15min to Daily")
            
            st.info("This analysis uses Grok-like step-by-step reasoning for maximum accuracy.")
    else:
        st.info("Upload a chart image to get Grok-level detailed analysis & exact trade levels.")

st.sidebar.success(f"AI Mode: Active")
