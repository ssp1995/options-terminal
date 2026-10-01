import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Algorithmic Options Engine", layout="wide", initial_sidebar_state="collapsed")

# Styling
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

# --- 1. INDEX SELECTION ---
INDEX_CONFIG = {
    "NIFTY 50 (NSE)": {"step": 50, "range": 500},
    "BANK NIFTY (NSE)": {"step": 100, "range": 1000},
    "SENSEX (BSE)": {"step": 100, "range": 1000},
    "FIN NIFTY (NSE)": {"step": 50, "range": 500},
    "MIDCP NIFTY (NSE)": {"step": 25, "range": 300},
    "BANKEX (BSE)": {"step": 100, "range": 1000},
}

selected_index = st.selectbox("Select Index", list(INDEX_CONFIG.keys()), index=0)
config = INDEX_CONFIG[selected_index]

# --- 2. LIVE DATA HOOK ---
# REPLACE THE CONTENTS OF THIS FUNCTION WITH YOUR ACTUAL BROKER / NSE CALL
@st.cache_data(ttl=3)
def fetch_live_data(index_name):
    """
    Replace this with your real API call:
    e.g. smartApi.optionGreek(...) or fyers.option_chain(...)
    Must return:
      spot (float)
      df with columns: ['strike', 'call_oi', 'call_ltp', 'put_oi', 'put_ltp']
    """
    # [Insert your broker's live API response here]
    # Ensure it returns the actual real-time spot and live chain dataframe:
    # return live_spot, live_df
    pass

# FALLBACK DEMO DATA (If your live API function is separate, link it directly here)
# Example structure your API should produce:
try:
    spot, full_df = fetch_live_data(selected_index)
except Exception:
    # Safe default dummy to prevent app from breaking before you link your API function
    if "SENSEX" in selected_index:
        spot = 72070.49
        base = 72000
        step = 100
    elif "BANK NIFTY" in selected_index:
        spot = 51420.00
        base = 51400
        step = 100
    else:  # Nifty 50 default
        spot = 25810.00  # realistic current market zone
        base = 25800
        step = 50

    strikes = [base + (i * step) for i in range(-5, 6)]
    demo_data = []
    for s in strikes:
        demo_data.append({
            "strike": s,
            "call_oi": abs(int((s - base + 200) * 15000 + 1500000)),
            "call_ltp": max(10.0, round(float(base + 250 - s) * 0.8, 2)),
            "put_oi": abs(int((base + 200 - s) * 14000 + 1400000)),
            "put_ltp": max(10.0, round(float(s - base + 250) * 0.7, 2))
        })
    full_df = pd.DataFrame(demo_data)

# --- 3. SANITIZATION & STRIKE FILTERING ---
full_df['strike'] = pd.to_numeric(full_df['strike'], errors='coerce')
full_df = full_df.dropna(subset=['strike']).sort_values(by="strike").reset_index(drop=True)

# Dynamic ATM calculation based on index step
atm_strike = int(round(spot / config["step"]) * config["step"])

# Filter strikes to a clean ± window around ATM to prevent single-bar scaling bugs
min_strike = atm_strike - config["range"]
max_strike = atm_strike + config["range"]
df = full_df[(full_df['strike'] >= min_strike) & (full_df['strike'] <= max_strike)].copy()

# In case filter was too tight, default to nearest 10 strikes
if len(df) < 5:
    df = full_df.copy()

# --- 4. ANALYTICS ---
total_put_oi = df['put_oi'].sum()
total_call_oi = df['call_oi'].sum()
pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi else 1.0

# Highest OI boundaries
support_strike = int(df.loc[df['put_oi'].idxmax()]['strike'])
resistance_strike = int(df.loc[df['call_oi'].idxmax()]['strike'])

is_bearish = pcr < 0.8
rec_action = "BUY PUT (PE)" if is_bearish else "BUY CALL (CE)"
target_strike = atm_strike

# Target strike lookup
atm_rows = df[df['strike'] == target_strike]
if not atm_rows.empty:
    entry_cmp = atm_rows.iloc[0]['put_ltp'] if is_bearish else atm_rows.iloc[0]['call_ltp']
else:
    # closest strike fallback
    closest_idx = (df['strike'] - target_strike).abs().idxmin()
    entry_cmp = df.loc[closest_idx, 'put_ltp' if is_bearish else 'call_ltp']

sl = round(entry_cmp * 0.72, 1)
t1 = round(entry_cmp * 1.25, 1)
t2 = round(entry_cmp * 1.50, 1)

# --- 5. UI DISPLAY ---
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

# --- 6. CHART RENDERING ---
st.markdown("#### 📊 Open Interest Distribution")

# Convert strikes strictly to string categories to guarantee equal spacing
df['strike_str'] = df['strike'].astype(int).astype(str)

fig = go.Figure()

# Red bars = Call OI
fig.add_trace(go.Bar(
    x=df['strike_str'],
    y=df['call_oi'],
    name='Call OI (Resistance)',
    marker_color='#ff4d4d'
))

# Green bars = Put OI
fig.add_trace(go.Bar(
    x=df['strike_str'],
    y=df['put_oi'],
    name='Put OI (Support)',
    marker_color='#26a69a'
))

# Spot Line marker
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
        text=f"Spot: {spot:,.0f}",
        showarrow=False,
        font=dict(color="#f1c40f", size=11),
        yshift=12
    )

fig.update_layout(
    barmode='group',
    template='plotly_dark',
    height=420,
    margin=dict(l=10, r=10, t=30, b=20),
    xaxis=dict(
        type='category',
        title="Strike",
        tickmode='linear'
    ),
    yaxis=dict(title="Open Interest"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)
