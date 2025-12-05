import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data

# 1. Load preprocessed data
@st.cache_data
def load_data():
    df = pd.read_csv("hiv_long.csv")
    df['iso_numeric'] = pd.to_numeric(df['iso_numeric'], errors='coerce')
    df['data_year'] = pd.to_numeric(df['data_year'], errors='coerce').astype('Int64')
    return df

hiv_long = load_data()

world_map = alt.topo_feature(data.world_110m.url, 'countries')

# 2. function of making a one-mode dashboard
def make_dashboard(mode: str):
    df_mode = hiv_long[hiv_long['mode'] == mode].copy()

    region_select = alt.selection_point(
        fields=['g_whoregion'],
        name='RegionSel'
    )

    map_chart = (
        alt.Chart(world_map)
        .mark_geoshape(stroke='white', strokeWidth=0.5)
        .transform_lookup(
            lookup='id',
            from_=alt.LookupData(
                df_mode,
                key='iso_numeric',
                fields=['country', 'g_whoregion', 'prev', 'data_year', 'source_type']
            )
        )
        .encode(
            color=alt.condition(
                alt.datum.prev != None,
                alt.Color(
                    'prev:Q',
                    title=f'HIV/TB prevalence (%) — {mode}',
                    scale=alt.Scale(scheme='oranges')
                ),
                alt.value('lightgray')
            ),
            opacity=alt.condition(
                region_select,
                alt.value(1.0),
                alt.value(0.4)
            ),
            tooltip=[
                alt.Tooltip('country:N',     title='Country'),
                alt.Tooltip('g_whoregion:N', title='WHO Region'),
                alt.Tooltip('prev:Q',        title='Prevalence (%)', format='.1f'),
                alt.Tooltip('source_type:N', title='Source'),
                alt.Tooltip('data_year:N',   title='Data year'),
            ]
        )
        .properties(
            width=650,
            height=350,
            title=f'HIV/TB Co-Infection Prevalence by Country ({mode})'
        )
        .project('equalEarth')
        .add_params(region_select)
    )

    box_chart = (
        alt.Chart(df_mode)
        .mark_boxplot(outliers=True)
        .encode(
            x=alt.X('g_whoregion:N', title='WHO Region'),
            y=alt.Y('prev:Q', title='HIV/TB prevalence (%)'),
            color=alt.condition(
                region_select,
                alt.Color('g_whoregion:N', title='WHO Region'),
                alt.value('lightgray')
            )
        )
        .properties(
            width=650,
            height=280,
            title=f'HIV/TB Prevalence by WHO Region ({mode})'
        )
    )

    return (map_chart & box_chart).resolve_scale(color='independent')


# 3. Streamlit
st.set_page_config(page_title="TB/HIV Co-infection Dashboard", layout="wide")

st.title("Global TB/HIV Co-infection Surveillance")
st.markdown(
    """
This dashboard visualizes HIV/TB co-infection prevalence using WHO non-routine surveillance data.
Use the selector below to switch between **Survey**, **Sentinel**, and **Combined** estimates.
"""
)

mode = st.radio(
    "Select data source for prevalence estimates:",
    options=["Combined", "Survey", "Sentinel"],
    index=0,
    horizontal=True
)

chart = make_dashboard(mode)
st.altair_chart(chart, use_container_width=True)

with st.expander("Show data summary for current mode"):
    df_mode = hiv_long[hiv_long['mode'] == mode].copy()
    st.write(f"Number of countries with data ({mode}): {df_mode['iso_numeric'].nunique()}")
    st.dataframe(
        df_mode[['country', 'g_whoregion', 'prev', 'data_year', 'source_type']].sort_values('g_whoregion')
    )