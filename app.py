import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Algorithmic Options Engine", layout="wide", initial_sidebar_state="collapsed")

# Custom Dark Theme Styling
st.markdown("""
<style>
    .signal-box-bearish {
        background-color: #3b181c;
        border: 1px solid #73232c;
        color: #ff9ca3;
        padding: 10px 14px;
        border-radius: 6px;
        font-weight: 500;
        margin-bottom: 12px;
    }
    .signal-box-bullish {
        background-color: #173623;
        border: 1px solid #236338;
        color: #85e3a3;
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

# --- 1. FULL INDEX SELECTOR ---
INDEX_LIST = [
    "SENSEX (BSE)",
    "NIFTY 50 (NSE)",
    "BANK NIFTY (NSE)",
    "FIN NIFTY (NSE)",
    "MIDCP NIFTY (NSE)",
    "BANKEX (BSE)"
]

selected_index = st.selectbox("Select Index", INDEX_LIST, index=0)

# --- 2. DATA PROVIDER ---
@st.cache_data(ttl=5)
def fetch_option_chain(index_name):
    """
    Returns (spot_price, dataframe, strike_interval)
    Replace these mock structures with your live broker API endpoint.
    """
    if "SENSEX" in index_name:
        spot = 72070.49
        step = 100
        chain = [
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
    elif "BANK NIFTY" in index_name:
        spot = 51200.00
        step = 100
        chain = [
            {"strike": 50900, "call_oi": 800000, "call_ltp": 420.0, "put_oi": 2500000, "put_ltp": 110.0},
            {"strike": 51000, "call_oi": 1200000, "call_ltp": 340.0, "put_oi": 3800000, "put_ltp": 160.0},
            {"strike": 51100, "call_oi": 1800000, "call_ltp": 260.0, "put_oi": 2900000, "put_ltp": 220.0},
            {"strike": 51200, "call_oi": 3100000, "call_ltp": 190.0, "put_oi": 2600000, "put_ltp": 290.0},
            {"strike": 51300, "call_oi": 4200000, "call_ltp": 130.0, "put_oi": 1800000, "put_ltp": 380.0},
            {"strike": 51400, "call_oi": 5100000, "call_ltp": 85.0, "put_oi": 1200000, "put_ltp": 490.0},
            {"strike": 51500, "call_oi": 6800000, "call_ltp": 50.0, "put_oi": 900000, "put_ltp": 610.0},
        ]
    elif "FIN NIFTY" in index_name:
        spot = 23850.00
        step = 50
        chain = [
            {"strike": 23700, "call_oi": 450000, "call_ltp": 185.0, "put_oi": 2100000, "put_ltp": 35.0},
            {"strike": 23750, "call_oi": 650000, "call_ltp": 145.0, "put_oi": 1800000, "put_ltp": 48.0},
            {"strike": 23800, "call_oi": 1200000, "call_ltp": 110.0, "put_oi": 2400000, "put_ltp": 68.0},
            {"strike": 23850, "call_oi": 1900000, "call_ltp": 78.0, "put_oi": 1700000, "put_ltp": 95.0},
            {"strike": 23900, "call_oi": 3100000, "call_ltp": 52.0, "put_oi": 1100000, "put_ltp": 135.0},
            {"strike": 23950, "call_oi": 2400000, "call_ltp": 32.0, "put_oi": 700000, "put_ltp": 180.0},
            {"strike": 24000, "call_oi": 4200000, "call_ltp": 18.0, "put_oi": 400000, "put_ltp": 240.0},
        ]
    elif "MIDCP NIFTY" in index_name:
        spot = 12900.00
        step = 25
        chain = [
            {"strike": 12825, "call_oi": 300000, "call_ltp": 95.0, "put_oi": 1400000, "put_ltp": 18.0},
            {"strike": 12850, "call_oi": 450000, "call_ltp": 76.0, "put_oi": 1800000, "put_ltp": 26.0},
            {"strike": 12875, "call_oi": 780000, "call_ltp": 58.0, "put_oi": 1500000, "put_ltp": 38.0},
            {"strike": 12900, "call_oi": 1600000, "call_ltp": 42.0, "put_oi": 1300000, "put_ltp": 52.0},
            {"strike": 12925, "call_oi": 2100000, "call_ltp": 29.0, "put_oi": 800000, "put_ltp": 72.0},
            {"strike": 12950, "call_oi": 2600000, "call_ltp": 19.0, "put_oi": 500000, "put_ltp": 98.0},
            {"strike": 12975, "call_oi": 1900000, "call_ltp": 11.0, "put_oi": 250000, "put_ltp": 130.0},
        ]
    elif "BANKEX" in index_name:
        spot = 58200.00
        step = 100
        chain = [
            {"strike": 57900, "call_oi": 150000, "call_ltp": 380.0, "put_oi": 850000, "put_ltp": 95.0},
            {"strike": 58000, "call_oi": 280000, "call_ltp": 310.0, "put_oi": 1200000, "put_ltp": 140.0},
            {"strike": 58100, "call_oi": 490000, "call_ltp": 240.0, "put_oi": 950000, "put_ltp": 190.0},
            {"strike": 58200, "call_oi": 950000, "call_ltp": 175.0, "put_oi": 850000, "put_ltp": 250.0},
            {"strike": 58300, "call_oi": 1400000, "call_ltp": 120.0, "put_oi": 550000, "put_ltp": 330.0},
            {"strike": 58400, "call_oi": 1700000, "call_ltp": 75.0, "put_oi": 350000, "put_ltp": 420.0},
            {"strike": 58500, "call_oi": 2200000, "call_ltp": 45.0, "put_oi": 200000, "put_ltp": 530.0},
        ]
    else:  # NIFTY 50
        spot = 24850.00
        step = 50
        chain = [
            {"strike": 24700, "call_oi": 1500000, "call_ltp": 210.0, "put_oi": 5200000, "put_ltp": 40.0},
            {"strike": 24750, "call_oi": 1800000, "call_ltp": 165.0, "put_oi": 4100000, "put_ltp": 58.0},
            {"strike": 24800, "call_oi": 3400000, "call_ltp": 125.0, "put_oi": 6200000, "put_ltp": 82.0},
            {"strike": 24850, "call_oi": 4900000, "call_ltp": 92.0, "put_oi": 4500000, "put_ltp": 115.0},
            {"strike": 24900, "call_oi": 7800000, "call_ltp": 62.0, "put_oi": 3100000, "put_ltp": 155.0},
            {"strike": 24950, "call_oi": 5600000, "call_ltp": 41.0, "put_oi": 1800000, "put_ltp": 205.0},
            {"strike": 25000, "call_oi": 9500000, "call_ltp": 25.0, "put_oi": 1400000, "put_ltp": 270.0},
        ]

    df = pd.DataFrame(chain)
    df['strike'] = df['strike'].astype(int)
    return spot, df.sort_values(by="strike").reset_index(drop=True), step

spot, df, strike_step = fetch_option_chain(selected_index)

# --- 3. ANALYTICS & EXECUTION LOGIC ---
atm_strike = int(round(spot / strike_step) * strike_step)
total_put_oi = df['put_oi'].sum()
total_call_oi = df['call_oi'].sum()
pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi else 1.0

support_strike = int(df.loc[df['put_oi'].idxmax()]['strike'])
resistance_strike = int(df.loc[df['call_oi'].idxmax()]['strike'])

is_bearish = pcr < 0.8
rec_action = "BUY PUT (PE)" if is_bearish else "BUY CALL (CE)"
target_strike = atm_strike

row = df[df['strike'] == target_strike]
if not row.empty:
    entry_cmp = row.iloc[0]['put_ltp'] if is_bearish else row.iloc[0]['call_ltp']
else:
    entry_cmp = df.iloc[len(df)//2]['put_ltp'] if is_bearish else df.iloc[len(df)//2]['call_ltp']

sl = round(entry_cmp * 0.72, 1)
t1 = round(entry_cmp * 1.25, 1)
t2 = round(entry_cmp * 1.50, 1)

# --- 4. DASHBOARD DISPLAY ---
st.title("⚡ Live Algorithmic Recommendation")

signal_class = "signal-box-bearish" if is_bearish else "signal-box-bullish"
dot_color = "🔴" if is_bearish else "🟢"
st.markdown(
    f"""<div class="{signal_class}">
        {dot_color} <b>Action:</b> {rec_action} | <b>Instrument:</b> {target_strike} {'PE' if is_bearish else 'CE'}
    </div>""", 
    unsafe_allow_html=True
)

c1, c2 = st.columns(2)
with c1:
    st.caption("Spot Index")
    st.subheader(f"₹{spot:,.2f}")
with c2:
    sentiment = "Bearish" if is_bearish else "Bullish"
    sent_color = "#ff6b6b" if is_bearish else "#51cf66"
    st.caption("Put-Call Ratio (PCR)")
    st.markdown(
        f"<h3 style='margin:0;'>{pcr} <span style='font-size:16px; color:{sent_color};'>● {sentiment}</span></h3>", 
        unsafe_allow_html=True
    )

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

# --- 5. OPEN INTEREST DISTRIBUTION CHART ---
st.markdown("#### 📊 Open Interest Distribution")

df['strike_str'] = df['strike'].astype(str)

fig = go.Figure()

fig.add_trace(go.Bar(
    x=df['strike_str'],
    y=df['call_oi'],
    name='Call OI (Resistance)',
    marker_color='#ff4d4d'
))

fig.add_trace(go.Bar(
    x=df['strike_str'],
    y=df['put_oi'],
    name='Put OI (Support)',
    marker_color='#26a69a'
))

# Safe categorical spot line using shapes instead of broken add_vline()
atm_str = str(atm_strike)
if atm_str in df['strike_str'].values:
    idx = df['strike_str'].tolist().index(atm_str)
    fig.add_shape(
        type="line",
        x0=idx, x1=idx,
        y0=0, y1=1,
        yref="paper",
        line=dict(color="#f1c40f", width=1.5, dash="dash")
    )
    fig.add_annotation(
        x=idx,
        y=1,
        yref="paper",
        text=f"Spot: {spot:.0f}",
        showarrow=False,
        font=dict(color="#f1c40f", size=11),
        yshift=10
    )

fig.update_layout(
    barmode='group',
    template='plotly_dark',
    height=400,
    margin=dict(l=10, r=10, t=35, b=20),
    xaxis=dict(type='category', title="Strike"),
    yaxis=dict(title="Open Interest"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)
