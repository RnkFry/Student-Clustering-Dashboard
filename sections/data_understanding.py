import streamlit as st

from src.eda_utils import data_dictionary
from src.ui_utils import filtered_source, render_dataset_metrics, require_visible_records


def render() -> None:
    st.subheader("Data Understanding")
    source = st.selectbox("Dataset", ["Raw", "Feature Engineering", "Reporting"], key="understanding_source")
    df = filtered_source(source)
    render_dataset_metrics(df)
    st.write("Granularitas: satu record mahasiswa–periode–mata kuliah–kelas. NIM dan kode merupakan identifier.")
    if not require_visible_records(df):
        return
    preview, dictionary = st.tabs(["Preview", "Data Dictionary"])
    with preview:
        limit = st.slider("Baris preview", 5, 100, 10, step=5, key="understanding_preview_rows")
        st.dataframe(df.head(limit), hide_index=True, width="stretch")
    with dictionary:
        st.dataframe(data_dictionary(df), hide_index=True, width="stretch")
        st.caption("Keterangan yang belum terverifikasi diberi penanda. Identifier tidak dimasukkan ke input model.")
