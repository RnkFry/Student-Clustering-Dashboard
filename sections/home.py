import streamlit as st

from src import config
from src.eda_utils import summarize_clusters
from src.ui_utils import cluster_label, reporting_view
from src.visualization import cluster_size_chart


def render() -> None:
    st.subheader("Home / Executive Summary")
    full, visible = reporting_view()
    cards = st.columns(4)
    cards[0].metric("Record pada filter", f"{len(visible):,}")
    cards[1].metric("NIM unik pada filter", f"{visible['NIM'].nunique():,}")
    cards[2].metric("Fitur input model", 8)
    cards[3].metric("Cluster model final", 4)
    st.caption(f"Seluruh reporting: {len(full):,} record dan {full['NIM'].nunique():,} NIM unik. Satu mahasiswa dapat memiliki beberapa record mata kuliah.")
    st.write("Metode: **K-Means** · Scaler: **RobustScaler** · K=4 dipilih manual.")
    metrics = st.columns(3)
    metrics[0].metric("Silhouette model final", f"{config.MODEL_METADATA['silhouette']:.5f}")
    metrics[1].metric("Davies-Bouldin", f"{config.MODEL_METADATA['davies_bouldin']:.5f}")
    metrics[2].metric("Calinski-Harabasz", f"{config.MODEL_METADATA['calinski_harabasz']:,.2f}")
    st.caption("Metrik evaluasi berasal dari model final pada seluruh data audit; angka ini tidak dihitung ulang ketika filter berubah.")
    summary = summarize_clusters(visible)
    cluster_size_chart(summary)
    table = summary[["Cluster", "Record_Count", "Record_Percentage", "Unique_NIM_Count"]].copy()
    table["Cluster"] = table["Cluster"].map(cluster_label)
    st.dataframe(table.round(2), hide_index=True, width="stretch")
    if len(visible):
        largest = summary.loc[summary["Record_Count"].idxmax()]
        st.write(f"Pada filter aktif, {cluster_label(int(largest['Cluster']))} memiliki jumlah record terbesar: {int(largest['Record_Count']):,} ({largest['Record_Percentage']:.2f}%).")
    else:
        st.info("Filter aktif tidak menghasilkan record. Ubah filter untuk melihat ringkasan.")
    st.write("Empat fitur LO dipakai untuk analisis deskriptif setelah clustering; perbedaannya tidak membuktikan hubungan sebab-akibat.")
    with st.expander("Keterbatasan dan provenance"):
        for note in config.KNOWN_LIMITATIONS:
            st.write(note)
        st.caption(f"Kontrak: {config.CONTRACT_VERSION}; label dibaca dari clustered_data.csv.")
