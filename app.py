"""Single-entry Streamlit MVP using immutable reporting labels."""

import streamlit as st

from sections import (
    home, data_understanding, eda_raw, feature_engineering, modeling_pipeline,
    cluster_analysis, cluster_interpretation, download_result,
)
from src.config import KNOWN_LIMITATIONS, ModelContractError
from src.data_loader import load_reporting_data
from src.ui_utils import render_sidebar_filters

SECTIONS = {
    "Home / Executive Summary": home,
    "Data Understanding": data_understanding,
    "EDA Raw Data": eda_raw,
    "Feature Engineering Result": feature_engineering,
    "Modeling Pipeline": modeling_pipeline,
    "Cluster Analysis": cluster_analysis,
    "Cluster Interpretation": cluster_interpretation,
    "Download Result": download_result,
}


def main() -> None:
    st.set_page_config(page_title="Student Clustering BINUS", layout="wide")
    st.title("Student Clustering BINUS")
    st.caption("Eksplorasi mahasiswa berdasarkan reporting model terverifikasi.")
    st.sidebar.title("Student Clustering Dashboard")
    st.sidebar.caption("K-Means · RobustScaler · F8 · K=4 manual")
    menu = st.sidebar.radio("Navigation", list(SECTIONS))
    st.warning("Catatan audit kualitas data: " + KNOWN_LIMITATIONS[0])
    try:
        reporting = load_reporting_data()
        render_sidebar_filters(reporting)
        SECTIONS[menu].render()
    except (ModelContractError, OSError) as exc:
        st.error(f"Validasi gagal: {exc}")
        st.stop()


if __name__ == "__main__":
    main()
