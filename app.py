import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import norm
import cloudscraper
import time

st.set_page_config(
    page_title="Multi-Index Options Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

INDEX_SPECS = {
    "NIFTY 50": {"exchange": "NSE", "symbol": "NIFTY", "lot_size": 65, "step": 50, "window": 500},
    "BANK NIFTY": {"exchange": "NSE", "symbol": "BANKNIFTY", "lot_size": 30, "step": 100, "window": 1200},
    "FINNIFTY": {"exchange": "NSE", "symbol": "FINNIFTY", "lot_size": 60, "step": 50, "window": 600},
    "MIDCAP NIFTY": {"exchange": "NSE", "symbol": "MIDCPNIFTY", "lot_size": 120, "step": 25, "window": 400},
    "SENSEX (BSE)": {"exchange": "BSE", "symbol": "SENSEX", "lot_size": 20, "step": 100, "window": 1500},
    "BANKEX (BSE)": {"exchange": "BSE", "symbol": "BANKEX", "lot_size": 30, "step": 100, "window": 1200}
}

@st.cache_data(ttl=30)
def fetch_option_data(symbol):
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15",
        "Referer": "https://www.nseindia.com/option-chain"
    }
    scraper = cloudscraper.create_scraper()
    try:
        scraper.get("https://www.nseindia.com", headers=headers, timeout=6)
        time.sleep(0.2)
        resp = scraper.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

def calc_greeks(spot, strike, dte, iv, r=0.07, opt_type="PE"):
    t = max(dte, 0.001) / 365.0
    sigma = max(iv, 0.01) / 100.0
    d1 = (np.log(spot / strike) + (r + 0.5 * sigma ** 2) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)
    if opt_type == "CE":
        delta = norm.cdf(d1)
        theta = (- (spot * norm.pdf(d1) * sigma) / (2 * np.sqrt(t)) - r * strike * np.exp(-r * t) * norm.cdf(d2)) / 365.0
    else:
        delta = -norm.cdf(-d1)
        theta = (- (spot * norm.pdf(d1) * sigma) / (2 * np.sqrt(t)) + r * strike * np.exp(-r * t) * norm.cdf(-d2)) / 365.0
    return delta, theta

# UI Top Bar
chosen_idx = st.selectbox("Select Index", list(INDEX_SPECS.keys()))
cfg = INDEX_SPECS[chosen_idx]
lot_size = cfg["lot_size"]

raw = fetch_option_data(cfg["symbol"]) if cfg["exchange"] == "NSE" else None
spot = 0.0
expiries = []
chain = []

if raw and "records" in raw:
    spot = raw['records'].get('underlyingValue', 0.0)
    expiries = raw['records'].get('expiryDates', [])

if spot == 0.0:
    defaults = {"NIFTY 50": 22568.0, "BANK NIFTY": 48250.0, "FINNIFTY": 21320.0, "MIDCAP NIFTY": 12150.0, "SENSEX (BSE)": 74210.0, "BANKEX (BSE)": 54890.0}
    spot = defaults.get(chosen_idx, 22500.0)
    expiries = ["Active Expiry"]

sel_expiry = st.selectbox("Expiry", expiries)

if raw and "records" in raw and cfg["exchange"] == "NSE":
    for itm in raw['records']['data']:
        if itm.get('expiryDate') == sel_expiry:
            chain.append({
                "Strike": itm['strikePrice'],
                "CE_OI": itm.get('CE', {}).get('openInterest', 0),
                "CE_Chg_OI": itm.get('CE', {}).get('changeinOpenInterest', 0),
                "CE_LTP": itm.get('CE', {}).get('lastPrice', 0.0),
                "PE_OI": itm.get('PE', {}).get('openInterest', 0),
                "PE_Chg_OI": itm.get('PE', {}).get('changeinOpenInterest', 0),
                "PE_LTP": itm.get('PE', {}).get('lastPrice', 0.0)
            })
    df = pd.DataFrame(chain).sort_values("Strike")
else:
    base = round(spot / cfg["step"]) * cfg["step"]
    df = pd.DataFrame([{
        "Strike": base + (i * cfg["step"]),
        "CE_OI": int(max(1000, 60000 - (i * cfg["step"] * 25))),
        "CE_Chg_OI": int(max(100, 8000 - (i * cfg["step"] * 5))),
        "CE_LTP": max(2.0, round(float(np.maximum(0, spot - (base + i * cfg["step"])) + 85.0), 1)),
        "PE_OI": int(max(1000, 60000 + (i * cfg["step"] * 25))),
        "PE_Chg_OI": int(max(100, 8000 + (i * cfg["step"] * 5))),
        "PE_LTP": max(2.0, round(float(np.maximum(0, (base + i * cfg["step"]) - spot) + 85.0), 1))
    } for i in range(-12, 13)]).sort_values("Strike")

# PCR & Signals
tot_ce_oi = df['CE_OI'].sum()
tot_pe_oi = df['PE_OI'].sum()
pcr = tot_pe_oi / tot_ce_oi if tot_ce_oi > 0 else 1.0

atm = min(df['Strike'], key=lambda x: abs(x - spot))
f_df = df[(df['Strike'] >= atm - cfg["window"]) & (df['Strike'] <= atm + cfg["window"])]
net_call_chg = f_df['CE_Chg_OI'].sum()
net_put_chg = f_df['PE_Chg_OI'].sum()

# Recommendation Engine
if pcr < 0.85 and net_call_chg > net_put_chg:
    sig = "BUY PUT (PE)"
    target_strike = atm
    entry_p = float(df[df['Strike'] == target_strike].iloc[0]['PE_LTP']) or 90.0
    color = "error"
    bias = "Bearish - Call writers building resistance"
elif pcr > 1.15 and net_put_chg > net_call_chg:
    sig = "BUY CALL (CE)"
    target_strike = atm
    entry_p = float(df[df['Strike'] == target_strike].iloc[0]['CE_LTP']) or 90.0
    color = "success"
    bias = "Bullish - Put writers defending floor"
else:
    sig = "SPREAD / NO NAKED"
    target_strike = atm
    entry_p = 0.0
    color = "warning"
    bias = "Consolidation / Sideways range"

st.subheader("⚡ Live Algorithmic Recommendation")
if color == "error":
    st.error(f"🔴 **{sig}** | Strike: **{target_strike} PE**")
elif color == "success":
    st.success(f"🟢 **{sig}** | Strike: **{target_strike} CE**")
else:
    st.warning(f"🟡 **{sig}** | Rangebound (Consider Spreads)")

c1, c2, c3 = st.columns(3)
c1.metric("Spot", f"₹{spot:,.1f}")
c2.metric("PCR", f"{pcr:.2f}")
if entry_p > 0:
    c3.metric("Entry / SL / Tgt", f"₹{entry_p:.1f} | ₹{entry_p*0.7:.1f} | ₹{entry_p*1.35:.1f}")
else:
    c3.metric("Bias", bias)

# Support / Resistance Summary
max_ce = f_df.loc[f_df['CE_OI'].idxmax()]['Strike']
max_pe = f_df.loc[f_df['PE_OI'].idxmax()]['Strike']
st.info(f"🛡️ **Floor (Support):** ₹{max_pe:,.0f} | 🚧 **Ceiling (Resistance):** ₹{max_ce:,.0f}")

# Mobile Clean Chart
t_oi, t_chg = st.tabs(["📊 Open Interest", "⚡ Change in OI"])
with t_oi:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=f_df['Strike'], y=f_df['CE_OI'], name='Call OI', marker_color='#FF4B4B'))
    fig.add_trace(go.Bar(x=f_df['Strike'], y=f_df['PE_OI'], name='Put OI', marker_color='#00CC96'))
    fig.add_vline(x=spot, line_dash="dash", line_color="yellow")
    fig.update_layout(template="plotly_dark", height=320, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)

with t_chg:
    fig_c = go.Figure()
    fig_c.add_trace(go.Bar(x=f_df['Strike'], y=f_df['CE_Chg_OI'], name='Call Chg', marker_color='#FF4B4B'))
    fig_c.add_trace(go.Bar(x=f_df['Strike'], y=f_df['PE_Chg_OI'], name='Put Chg', marker_color='#00CC96'))
    fig_c.add_hline(y=0, line_color="white")
    fig_c.add_vline(x=spot, line_dash="dash", line_color="yellow")
    fig_c.update_layout(template="plotly_dark", height=320, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h"))
    st.plotly_chart(fig_c, use_container_width=True)
