"""Shared display filters; these functions never assign or predict cluster labels."""

import pandas as pd
import streamlit as st

from src import config
from src.data_loader import load_feature_engineered_data, load_raw_data, load_reporting_data

FILTER_KEYS = ("filter_periods", "filter_courses", "filter_classes", "filter_clusters")


def cluster_label(cluster: int) -> str:
    return f"Cluster {cluster}"


def apply_reporting_filters(df: pd.DataFrame, *, periods=(), courses=(), classes=(), clusters=None) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    for column, selected in (("Kode_Periode", periods), ("Kode Mata kuliah", courses), ("Kode Kelas", classes)):
        if selected:
            mask &= df[column].isin(selected)
    if clusters is not None:
        mask &= df[config.CLUSTER_COLUMN].isin(clusters)
    return df.loc[mask].copy()


def reset_filters() -> None:
    for key in FILTER_KEYS[:3]:
        st.session_state[key] = []
    st.session_state[FILTER_KEYS[3]] = list(range(4))


def render_sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.subheader("Filter tampilan")
    for column, label, key in (
        ("Kode_Periode", "Periode", FILTER_KEYS[0]),
        ("Kode Mata kuliah", "Mata kuliah", FILTER_KEYS[1]),
        ("Kode Kelas", "Kelas", FILTER_KEYS[2]),
    ):
        st.sidebar.multiselect(label, sorted(df[column].dropna().unique().tolist()), key=key,
                              help="Kosong berarti semua. Filter ini berlaku pada seluruh menu.")
    if FILTER_KEYS[3] not in st.session_state:
        st.session_state[FILTER_KEYS[3]] = list(range(4))
    st.sidebar.multiselect("Cluster", list(range(4)), format_func=cluster_label,
                          key=FILTER_KEYS[3], help="Pilih cluster yang ingin ditampilkan.")
    st.sidebar.button("Reset filter", on_click=reset_filters)
    filtered = apply_reporting_filters(df, **current_filters())
    st.sidebar.caption(f"Tampilan: {len(filtered):,} / {len(df):,} record; {filtered['NIM'].nunique():,} NIM unik.")
    st.sidebar.caption("Label cluster berasal dari reporting tersimpan.")
    return filtered


def current_filters() -> dict:
    return dict(periods=st.session_state.get(FILTER_KEYS[0], []), courses=st.session_state.get(FILTER_KEYS[1], []),
                classes=st.session_state.get(FILTER_KEYS[2], []), clusters=st.session_state.get(FILTER_KEYS[3], list(range(4))))


def reporting_view() -> tuple[pd.DataFrame, pd.DataFrame]:
    full = load_reporting_data()
    return full, apply_reporting_filters(full, **current_filters())


def filtered_source(source: str) -> pd.DataFrame:
    full, visible = reporting_view()
    if source == "Reporting":
        return visible
    df = load_raw_data() if source == "Raw" else load_feature_engineered_data()
    if not df[list(config.IDENTIFIER_COLUMNS)].equals(full[list(config.IDENTIFIER_COLUMNS)]):
        raise config.ModelContractError("Identifier/urutan sumber berbeda dari reporting.")
    return df.loc[visible.index].copy()


def require_visible_records(df: pd.DataFrame) -> bool:
    if df.empty:
        st.info("Tidak ada record yang cocok dengan filter. Ubah pilihan atau gunakan Reset filter.")
        return False
    return True


def render_dataset_metrics(df: pd.DataFrame) -> None:
    columns = st.columns(3)
    columns[0].metric("Jumlah record", f"{len(df):,}")
    columns[1].metric("NIM unik", f"{df['NIM'].nunique():,}")
    columns[2].metric("Jumlah kolom", df.shape[1])
    st.caption("Angka mengikuti filter aktif. Satu NIM dapat memiliki beberapa record mata kuliah.")
