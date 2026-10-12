import streamlit as st

from src.eda_utils import descriptive_statistics, missing_summary, numerical_columns, outlier_summary
from src.ui_utils import filtered_source, render_dataset_metrics, require_visible_records
from src.visualization import boxplot, histogram, render_correlation


def render() -> None:
    st.subheader("EDA Raw Data")
    df = filtered_source("Raw")
    render_dataset_metrics(df)
    if not require_visible_records(df):
        return
    overview, missing, stats, distribution, outliers, correlation = st.tabs([
        "Overview", "Missing & Duplicate", "Descriptive Statistics", "Distribution", "Outlier", "Correlation"
    ])
    numerical = numerical_columns(df)
    with overview:
        st.dataframe(df.head(10), hide_index=True, width="stretch")
        st.dataframe(df.dtypes.astype(str).rename("Tipe").to_frame(), width="stretch")
    with missing:
        st.metric("Duplikasi seluruh baris", int(df.duplicated().sum()))
        st.dataframe(missing_summary(df), hide_index=True, width="stretch")
        st.info("Missing timestamp terkait tugas tanpa timestamp pengumpulan. Audit menemukan 1.477 sel missing pada enam timestamp di seluruh raw data.")
    with stats:
        st.dataframe(descriptive_statistics(df).round(3), width="stretch")
        st.caption("Statistik hanya memakai variabel numerik; NIM/kode tidak diperlakukan sebagai besaran numerik.")
    with distribution:
        feature = st.selectbox("Fitur distribusi raw", numerical, key="raw_distribution_feature")
        histogram(df, feature)
    with outliers:
        feature = st.selectbox("Fitur boxplot raw", numerical, key="raw_boxplot_feature")
        boxplot(df, feature)
        st.dataframe(outlier_summary(df).round(3), hide_index=True, width="stretch")
        st.caption("Aturan 1,5 × IQR menandai record ekstrem; ini tidak otomatis berarti data salah.")
    with correlation:
        render_correlation(df, numerical, key="raw_correlation_features")
