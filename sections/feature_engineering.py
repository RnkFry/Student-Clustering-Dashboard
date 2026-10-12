import streamlit as st

from src import config
from src.eda_utils import data_dictionary, descriptive_statistics
from src.ui_utils import filtered_source, render_dataset_metrics, require_visible_records
from src.visualization import histogram, render_correlation


def render() -> None:
    st.subheader("Feature Engineering Result")
    df = filtered_source("Feature Engineering")
    render_dataset_metrics(df)
    st.write("**8 fitur input model**, mengikuti urutan kontrak:")
    st.code("\n".join(f"{i+1}. {feature}" for i, feature in enumerate(config.MODEL_FEATURES)), language=None)
    st.write("**4 fitur analisis eksternal:** " + ", ".join(config.LO_FEATURES))
    st.caption("Fitur LO tidak masuk scaler/model clustering. Total_LO adalah jumlah tiga avg_LO.")
    if not require_visible_records(df):
        return
    preview, statistics, distribution, correlation = st.tabs(["Preview & Features", "Statistics", "Distribution", "Correlation"])
    with preview:
        st.dataframe(df.head(10), hide_index=True, width="stretch")
        st.dataframe(data_dictionary(df), hide_index=True, width="stretch")
    with statistics:
        st.dataframe(descriptive_statistics(df).round(3), width="stretch")
        st.write(f"Missing pada tampilan aktif: {int(df.isna().sum().sum())} sel.")
    with distribution:
        feature = st.selectbox("Fitur distribusi FE", list(config.MODEL_FEATURES + config.LO_FEATURES), key="fe_distribution_feature")
        histogram(df, feature)
    with correlation:
        render_correlation(df, list(config.MODEL_FEATURES + config.LO_FEATURES), key="fe_correlation_features")
