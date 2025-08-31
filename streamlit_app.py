# app.py
# Minimal data-focused Streamlit starter demonstrating:
# - sidebar filters
# - caching
# - session_state
# - KPI row + tabs
# - empty/error states
# Run: streamlit run app.py

from datetime import date, timedelta
import pandas as pd
import numpy as np
import streamlit as st

# ---------- Page setup ----------
st.set_page_config(page_title="Streamlit Data App — Starter", page_icon="📊", layout="wide")

st.title("📊 Streamlit Data App — Starter")
st.caption("Learn the core patterns (reruns, caching, state, layout) before adding real APIs like Dune.")

# ---------- Demo dataset (cached) ----------
@st.cache_data(ttl=600)
def load_mock(days=60, projects=("uniswap","aave","curve","balancer")) -> pd.DataFrame:
    """Expensive work (simulated) should go behind cache_data. Returns a tidy DataFrame."""
    rng = pd.date_range(end=pd.Timestamp.utcnow().normalize(), periods=days, freq="D")
    df = pd.DataFrame({
        "day": np.repeat(rng, len(projects)),
        "project": projects * len(rng),
    })
    # fake metrics
    rs = np.random.default_rng(42)
    df["tx_count"] = rs.integers(800, 3000, size=len(df))
    df["amount_usd"] = (df["tx_count"] * rs.uniform(0.5, 2.0, size=len(df))).round(2)
    return df

# ---------- Session state example ----------
if "ack_walkthrough" not in st.session_state:
    st.session_state.ack_walkthrough = False

with st.expander("What’s happening under the hood?"):
    st.markdown(
        "- Changing any widget triggers a **rerun** of this script.\n"
        "- Heavy work (like HTTP calls) is protected by **@st.cache_data**.\n"
        "- We store simple flags in **st.session_state** to persist UI choices across reruns."
    )
    if not st.session_state.ack_walkthrough:
        if st.button("Got it"):
            st.session_state.ack_walkthrough = True
            st.toast("Nice—let’s build!", icon="✅")

# ---------- Sidebar filters ----------
st.sidebar.header("Filters")
days = st.sidebar.slider("Days of history", 7, 180, 60, help="Affects the cached data loader above.")
all_projects = ["uniswap","aave","curve","balancer","sushiswap"]
selected = st.sidebar.multiselect("Projects", all_projects, default=["uniswap","aave","curve"])
d2 = date.today()
d1 = st.sidebar.date_input("Date range", value=(d2 - timedelta(days=days-1), d2))

# Load & filter data (fast because cached)
df = load_mock(days=days, projects=tuple(selected) if selected else tuple(all_projects))

# Client-side date filter
df = df[(df["day"].dt.date >= d1[0]) & (df["day"].dt.date <= d1[-1])]

# ---------- Empty/validation states ----------
if not selected:
    st.info("Select at least one project in the sidebar.", icon="👉")
    st.stop()

if df.empty:
    st.warning("No rows for this date range.", icon="🗓️")
    st.stop()

# ---------- KPI row ----------
st.subheader("Key metrics")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Rows", f"{len(df):,}")
with c2:
    st.metric("Projects", df["project"].nunique())
with c3:
    st.metric("Date coverage", f"{df['day'].min().date()} → {df['day'].max().date()}")
with c4:
    st.metric("Σ Volume (USD)", f"${df['amount_usd'].sum():,.0f}")

# ---------- Tabs ----------
t_chart, t_table, t_break, t_about = st.tabs(["📈 Charts", "📋 Table", "🔎 Breakdowns", "ℹ️ About"])

with t_chart:
    import altair as alt
    # Area chart of total amount_usd over time
    daily = df.groupby("day", as_index=False)["amount_usd"].sum()
    st.altair_chart(
        alt.Chart(daily).mark_area().encode(
            x="day:T", y=alt.Y("amount_usd:Q", title="USD"), tooltip=["day","amount_usd"]
        ).interactive(),
        use_container_width=True
    )

with t_table:
    st.caption("Tip: use the column menu to sort and filter.")
    st.dataframe(df.sort_values("day"), use_container_width=True, hide_index=True)
    st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"),
                       file_name="data.csv", mime="text/csv")

with t_break:
    # Simple “group by” UI pattern
    dim = st.selectbox("Dimension", ["project"])
    metric = st.selectbox("Metric", ["amount_usd","tx_count"])
    topn = st.slider("Top N", 5, 50, 10)
    g = df.groupby(dim, as_index=False)[metric].sum().sort_values(metric, ascending=False).head(topn)
    st.bar_chart(g.set_index(dim)[metric], use_container_width=True)
    st.dataframe(g, use_container_width=True, hide_index=True)

with t_about:
    st.markdown(
        "- **Reruns:** widgets → rerun script → render new view.\n"
        "- **Cache:** `@st.cache_data` keeps fetch/transform results warm.\n"
        "- **State:** `st.session_state` remembers choices.\n"
        "- **Layout:** sidebar for inputs, tabs for surfaces, KPIs up top."
    )
