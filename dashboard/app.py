import streamlit as st, pandas as pd, pathlib, glob

DATA_DIR = pathlib.Path("data")
SLIPS_FILE = DATA_DIR / "slips_history.json"

def _load():
    if SLIPS_FILE.exists():
        return pd.read_json(SLIPS_FILE).astype(
            {"date": "datetime64[ns]", "slip_type": "category", "tag": "category"}
        )
    files = sorted(pathlib.Path(".").glob("edge_sheet_*.csv"))
    return pd.read_csv(files[-1]) if files else pd.DataFrame()

def _filters(df):
    if df.empty:
        return df
    st.sidebar.markdown("### Filters")
    if "slip_type" in df.columns:
        types = st.sidebar.multiselect(
            "Slip type",
            sorted(df["slip_type"].unique()),
            default=list(df["slip_type"].unique()),
        )
        if types:
            df = df[df["slip_type"].isin(types)]
    if "tag" in df.columns:
        tags = st.sidebar.multiselect(
            "Tag", sorted(df["tag"].unique()), default=list(df["tag"].unique())
        )
        if tags:
            df = df[df["tag"].isin(tags)]
    if "date" in df.columns:
        after = st.sidebar.date_input("After", value=df["date"].min().date())
        df = df[df["date"] >= pd.Timestamp(after)]
    return df

def _pl_cards(df):
    if {"stake", "payout"}.issubset(df.columns):
        staked = df["stake"].sum()
        returned = df["payout"].sum()
        profit = returned - staked
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Staked", f"${staked:,.2f}")
        col2.metric("Total Returned", f"${returned:,.2f}")
        pct = f"{(profit / staked * 100):.2f} %" if staked else "0 %"
        col3.metric("P/L", f"${profit:,.2f}", delta=pct)

def main():
    st.set_page_config(page_title="PP-EDGE Dashboard", layout="wide")
    df = _load()
    if df.empty:
        st.error("No slips or edge sheets found.")
        return
    df = _filters(df)
    st.dataframe(df, use_container_width=True)
    _pl_cards(df)
    if {"tier", "edge_pp"}.issubset(df.columns):
        agg = (
            df.groupby("tier")["edge_pp"]
            .agg(["count", "mean"])
            .reset_index()
            .rename(columns={"mean": "edge_mean"})
        )
        st.subheader("Edge by Tier")
        st.table(agg)

if __name__ == "__main__":
    main()
