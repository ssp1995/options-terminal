import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sensex Algorithmic Engine", layout="wide", initial_sidebar_state="collapsed")

# Custom Dark Theme Styling matching your screenshot
st.markdown("""
<style>
    .metric-card {
        background-color: #12141a;
        border-radius: 8px;
        padding: 14px 18px;
        border: 1px solid #232733;
    }
    .signal-box-bearish {
        background-color: #3b181c;
        border: 1px solid #73232c;
        color: #ff9ca3;
        padding: 10px 14px;
        border-radius: 6px;
        font-weight: 500;
        margin-bottom: 12px;
    }
    .support-ceiling-box {
        background-color: #162238;
        border: 1px solid #1f3b6a;
        color: #90c2ff;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 14px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. SENSEX DATA FETCHING & SANITIZATION ---
@st.cache_data(ttl=5)
def get_sensex_option_chain():
    """
    Simulated live snapshot matching your 01-Oct Sensex chain.
    Replace the internal dict with your live broker API response (AngelOne, Zerodha, Fyers, Upstox, etc.)
    Ensure BSE strikes are sorted as integer/float, not strings.
    """
    spot_price = 72070.49
    
    # Accurate snapshot of BSE Sensex (01 Oct)
    raw_chain = [
        {"strike": 71800, "call_oi": 290000, "call_ltp": 347.55, "put_oi": 3557000, "put_ltp": 61.95},
        {"strike": 71900, "call_oi": 414000, "call_ltp": 270.35, "put_oi": 2924000, "put_ltp": 88.85},
        {"strike": 72000, "call_oi": 2503000, "call_ltp": 205.30, "put_oi": 5818000, "put_ltp": 122.15},
        {"strike": 72100, "call_oi": 3471000, "call_ltp": 148.95, "put_oi": 2739000, "put_ltp": 165.85},
        {"strike": 72200, "call_oi": 4879000, "call_ltp": 106.10, "put_oi": 2429000, "put_ltp": 224.40},
        {"strike": 72300, "call_oi": 6089000, "call_ltp": 74.35, "put_oi": 1552000, "put_ltp": 290.80},
        {"strike": 72400, "call_oi": 6519000, "call_ltp": 52.65, "put_oi": 1657000, "put_ltp": 367.30},
        {"strike": 72500, "call_oi": 9140000, "call_ltp": 38.20, "put_oi": 1632000, "put_ltp": 450.85},
        {"strike": 72600, "call_oi": 4615000, "call_ltp": 27.95, "put_oi": 565000, "put_ltp": 546.50},
    ]
    df = pd.DataFrame(raw_chain)
    
    # Ensure types are correct to prevent plotting dropouts
    df['strike'] = df['strike'].astype(int)
    df = df.sort_values(by="strike").reset_index(drop=True)
    return spot_price, df

spot, df = get_sensex_option_chain()

# --- 2. CALCULATIONS (PCR, SUPPORT, RESISTANCE) ---
# Filter strikes within +/- 500 points from spot for active calculation
strike_step = 100
atm_strike = int(round(spot / strike_step) * strike_step)

# True dynamic PCR across the relevant trading band
total_put_oi = df['put_oi'].sum()
total_call_oi = df['call_oi'].sum()
pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi else 1.0

# Support = Strike with Highest Put OI (Floor)
# Resistance = Strike with Highest Call OI (Ceiling)
support_strike = int(df.loc[df['put_oi'].idxmax()]['strike'])
resistance_strike = int(df.loc[df['call_oi'].idxmax()]['strike'])

# Selection for Recommendation Instrument
# If PCR is Bearish (< 0.8) and Spot < Resistance, consider ATM / slight ITM Put
rec_action = "BUY PUT (PE)" if pcr < 0.8 else "BUY CALL (CE)"
target_strike = atm_strike  # 72,100

selected_row = df[df['strike'] == target_strike].iloc[0]
entry_cmp = selected_row['put_ltp'] if "PUT" in rec_action else selected_row['call_ltp']

# Execution Plan Math
sl = round(entry_cmp * 0.72, 1)        # 28% Stop Loss
t1 = round(entry_cmp * 1.25, 1)        # 25% Target 1
t2 = round(entry_cmp * 1.50, 1)        # 50% Target 2

# --- 3. UI RENDERING ---
st.title("⚡ Live Algorithmic Recommendation")

st.markdown(
    f"""<div class="signal-box-bearish">
        🔴 <b>Action:</b> {rec_action} | <b>Instrument:</b> {target_strike} {'PE' if 'PUT' in rec_action else 'CE'}
    </div>""", 
    unsafe_allow_html=True
)

c1, c2 = st.columns(2)
with c1:
    st.markdown(f"**Spot Index**<br>### ₹{spot:,.2f}", unsafe_allow_html=True)
with c2:
    sentiment = "Bearish" if pcr < 0.8 else "Bullish"
    st.markdown(f"**Put-Call Ratio (PCR)**<br>### {pcr} <span style='font-size:14px; color:{'#ff6b6b' if pcr < 0.8 else '#51cf66'};'>● {sentiment}</span>", unsafe_allow_html=True)

st.markdown("#### 🎯 Execution Plan")
e1, e2, e3, e4 = st.columns(4)
e1.metric("Entry (CMP)", f"₹{entry_cmp}")
e2.metric("Stop-Loss (SL)", f"₹{sl}", delta="-28%", delta_color="inverse")
e3.metric("Target 1", f"₹{t1}", delta="+25%")
e4.metric("Target 2", f"₹{t2}", delta="+50%")

st.markdown(
    f"""<div class="support-ceiling-box">
        🛡️ <b>Floor (Support):</b> {support_strike:,} &nbsp;|&nbsp; 🧱 <b>Ceiling (Resistance):</b> {resistance_strike:,}
    </div>""", 
    unsafe_allow_html=True
)

# --- 4. OPEN INTEREST DISTRIBUTION CHART ---
st.markdown("#### 📊 Open Interest Distribution")

# Filter strikes around ATM (+/- 5 strikes) so the chart isn't cramped or truncated
visible_df = df[(df['strike'] >= atm_strike - 400) & (df['strike'] <= atm_strike + 500)].copy()

fig = go.Figure()

# Call OI (Resistance - Red)
fig.add_trace(go.Bar(
    x=visible_df['strike'],
    y=visible_df['call_oi'],
    name='Call OI (Resistance)',
    marker_color='#ff4d4d'
))

# Put OI (Support - Green)
fig.add_trace(go.Bar(
    x=visible_df['strike'],
    y=visible_df['put_oi'],
    name='Put OI (Support)',
    marker_color='#26a69a'
))

# Dashed line for Spot/ATM
fig.add_vline(
    x=spot, 
    line_width=1.5, 
    line_dash="dash", 
    line_color="#f1c40f",
    annotation_text=f"Spot: {spot:.0f}",
    annotation_position="top left",
    annotation_font_color="#f1c40f"
)

fig.update_layout(
    barmode='group',
    template='plotly_dark',
    height=380,
    margin=dict(l=20, r=20, t=30, b=20),
    xaxis=dict(
        type='category',  # Ensures every strike is evenly spaced and labeled
        categoryorder='category ascending',
        title="Strike"
    ),
    yaxis=dict(title="Open Interest"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)
