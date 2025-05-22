import streamlit as st, pandas as pd, pathlib, glob

def _latest_edge_sheet():
    files = sorted(pathlib.Path('.').glob('edge_sheet_*.csv'))
    return files[-1] if files else None

def main():
    st.title('PP-EDGE Dashboard')
    path = _latest_edge_sheet()
    if not path:
        st.error('No edge sheets found.')
        return
    df = pd.read_csv(path)
    st.caption(f'Loaded {path.name} • {len(df)} rows')
    st.dataframe(df, use_container_width=True)
    if 'tier' in df.columns and 'edge_pp' in df.columns:
        agg = (df.groupby('tier')['edge_pp']
                 .agg(['count','mean'])
                 .reset_index()
                 .rename(columns={'mean':'edge_mean'}))
        st.subheader('Edge by Tier')
        st.table(agg)
if __name__ == '__main__':
    main()
