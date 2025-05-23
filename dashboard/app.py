import streamlit as st, pandas as pd, pathlib
DATA_DIR = pathlib.Path("data")
SLIPS_FILE = DATA_DIR / "slips_history.json"
def _load():
    if SLIPS_FILE.exists():
        return pd.read_json(SLIPS_FILE).astype({"date":"datetime64[ns]","slip_type":"category","tag":"category"})
    f = sorted(pathlib.Path(".").glob("edge_sheet_*.csv"))
    return pd.read_csv(f[-1]) if f else pd.DataFrame()
def _filters(df):
    if df.empty: return df
    st.sidebar.markdown("### Filters")
    if "slip_type" in df.columns:
        t = st.sidebar.multiselect("Slip type", sorted(df["slip_type"].unique()), default=list(df["slip_type"].unique()))
        if t: df = df[df["slip_type"].isin(t)]
    if "tag" in df.columns:
        g = st.sidebar.multiselect("Tag", sorted(df["tag"].unique()), default=list(df["tag"].unique()))
        if g: df = df[df["tag"].isin(g)]
    if "date" in df.columns:
        after = st.sidebar.date_input("After", value=df["date"].min().date())
        df = df[df["date"] >= pd.Timestamp(after)]
    return df
def _pl(df):
    if {"stake","payout"}.issubset(df.columns):
        s = df["stake"].sum(); r = df["payout"].sum(); p = r - s
        c1,c2,c3 = st.columns(3)
        c1.metric("Total Staked", f"${s:,.2f}")
        c2.metric("Total Returned", f"${r:,.2f}")
        c3.metric("P/L", f"${p:,.2f}", delta=f"{(p/s*100):.2f} %" if s else "0 %")
def main():
    st.set_page_config(page_title="PP-EDGE Dashboard", layout="wide")
    df = _load()
    if df.empty: st.error("No slips or edge sheets found."); return
    df = _filters(df)
    st.dataframe(df, use_container_width=True)
    _pl(df)
    if {"tier","edge_pp"}.issubset(df.columns):
        agg = df.groupby("tier")["edge_pp"].agg(["count","mean"]).reset_index().rename(columns={"mean":"edge_mean"})
        st.subheader("Edge by Tier"); st.table(agg)
if __name__ == "__main__": main()
