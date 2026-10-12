import streamlit as st

from src import config
from src.eda_utils import summarize_clusters
from src.ui_utils import cluster_label, render_dataset_metrics, reporting_view, require_visible_records
from src.visualization import boxplot, cluster_size_chart, heatmap, pca_chart, radar_chart


def render() -> None:
    st.subheader("Cluster Analysis")
    full, visible = reporting_view()
    render_dataset_metrics(visible)
    st.caption("Sumber: clustered_data.csv. Semua label mengikuti reporting tersimpan.")
    if not require_visible_records(visible):
        return
    summary = summarize_clusters(visible)
    counts, profile, radar, projection, distribution = st.tabs(["Cluster Size", "Feature Profile", "Radar", "PCA 2D", "Distribution"])
    with counts:
        cluster_size_chart(summary)
        table = summary[["Cluster", "Record_Count", "Record_Percentage", "Unique_NIM_Count"]].copy()
        table["Cluster"] = table["Cluster"].map(cluster_label)
        st.dataframe(table.round(2), hide_index=True, width="stretch")
        st.caption("NIM dapat muncul di lebih dari satu cluster melalui record berbeda; NIM unik per cluster tidak boleh dijumlahkan sebagai total mahasiswa.")
    means = visible.groupby("Cluster")[list(config.MODEL_FEATURES)].mean().reindex(range(4))
    with profile:
        labeled = means.copy()
        labeled.index = labeled.index.map(cluster_label)
        heatmap(labeled, domain=[0, 100], title="Rata-rata (%)")
        st.dataframe(labeled.round(3), width="stretch")
        st.write("LO sebagai profil eksternal:")
        external = visible.groupby("Cluster")[list(config.LO_FEATURES)].mean().reindex(range(4))
        external.index = external.index.map(cluster_label)
        st.dataframe(external.round(3), width="stretch")
        st.caption("Perbedaan nilai LO bersifat deskriptif dan tidak membuktikan bahwa cluster menyebabkan perubahan nilai.")
    with radar:
        radar_chart(means)
    with projection:
        pca_chart(full, visible)
    with distribution:
        feature = st.selectbox("Fitur berdasarkan cluster", list(config.MODEL_FEATURES + config.LO_FEATURES), key="cluster_distribution_feature")
        boxplot(visible, feature, by_cluster=True)
