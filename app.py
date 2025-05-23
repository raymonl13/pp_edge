import pathlib, datetime, pandas as pd, streamlit as st

_ROOT = pathlib.Path(__file__).resolve().parent
_SLIP_CSV = _ROOT / "data" / "slip_results.csv"
_KPI_DIR = _ROOT / "analytics"

def _load_slips() -> pd.DataFrame:
    if _SLIP_CSV.exists():
        df = pd.read_csv(_SLIP_CSV)
        df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")
        return df
    return pd.DataFrame(columns=["slip_id","status","payout","tier","updated_at"])

def _latest_kpi() -> pd.DataFrame:
    files = sorted(_KPI_DIR.glob("tier_kpi_*.csv"))
    if files:
        return pd.read_csv(files[-1])
    return pd.DataFrame(columns=["date","tier","total","wins","losses","win_rate","pnl","var_95"])

def main() -> None:
    st.set_page_config(page_title="PP-EDGE Dashboard", layout="wide")
    st.title("PP-EDGE Live Results & Tier KPIs")
    df = _load_slips()
    kpi = _latest_kpi()
    tier_sel = st.multiselect("Filter by tier", options=sorted(df["tier"].unique()), default=sorted(df["tier"].unique()))
    date_sel = st.date_input("Start date", value=datetime.date.today() - datetime.timedelta(days=7))
    df_f = df[(df["tier"].isin(tier_sel)) & (df["updated_at"].dt.date >= date_sel)]
    st.subheader("Live Results")
    st.dataframe(df_f.sort_values("updated_at", ascending=False), use_container_width=True)
    st.subheader("Tier KPIs")
    kpi_f = kpi[kpi["tier"].isin(tier_sel)]
    cols = st.columns(len(kpi_f))
    for i, (_, r) in enumerate(kpi_f.iterrows()):
        with cols[i]:
            st.metric(label=f"{r['tier']} P/L", value=f"{r['pnl']:+.2f}")
            st.metric(label="Win Rate", value=f"{r['win_rate']*100:.1f}%")

if __name__ == "__main__":
    main()
