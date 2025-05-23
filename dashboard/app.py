import json, pathlib, pandas as pd, streamlit as st

DATA_DIR = pathlib.Path("data")
SLIPS_FILE = DATA_DIR / "slips_history.json"

def _load() -> pd.DataFrame:
    if not SLIPS_FILE.exists():
        return pd.DataFrame(columns=["date", "slip_type", "tag", "stake", "payout"])
    return pd.read_json(SLIPS_FILE).astype(
        {"date": "datetime64[ns]", "slip_type": "category", "tag": "category"}
    )

def _filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.markdown("### Filters")
    types = st.sidebar.multiselect("Slip type", sorted(df["slip_type"].unique()), default=list(df["slip_type"].unique()))
    tags = st.sidebar.multiselect("Tag", sorted(df["tag"].unique()), default=list(df["tag"].unique()))
    after = st.sidebar.date_input("After", value=df["date"].min().date() if not df.empty else None)
    if types:
        df = df[df["slip_type"].isin(types)]
    if tags:
        df = df[df["tag"].isin(tags)]
    if after:
        df = df[df["date"] >= pd.Timestamp(after)]
    return df

def _pl_cards(df: pd.DataFrame) -> None:
    col1, col2, col3 = st.columns(3)
    staked = df["stake"].sum()
    returned = df["payout"].sum()
    profit = returned - staked
    col1.metric("Total Staked", f"${staked:,.2f}")
    col2.metric("Total Returned", f"${returned:,.2f}")
    col3.metric("P/L", f"${profit:,.2f}", delta=f"{(profit / staked * 100):.2f} %" if staked else "0 %")

def main() -> None:
    st.set_page_config(page_title="PP-EDGE Dashboard", layout="wide")
    df = _load()
    df = _filters(df)
    st.header("Filtered Slips")
    st.dataframe(df)
    _pl_cards(df)

if __name__ == "__main__":
    main()
