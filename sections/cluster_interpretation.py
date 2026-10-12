import pandas as pd
import streamlit as st

from src import config
from src.ui_utils import cluster_label, reporting_view, require_visible_records


def render() -> None:
    st.subheader("Cluster Interpretation")
    full, visible = reporting_view()
    st.info("Nama sementara: Cluster 0, Cluster 1, Cluster 2, Cluster 3. Persona final menunggu validasi akademik.")
    if not require_visible_records(visible):
        return
    cluster = st.selectbox("Cluster untuk profil", list(range(4)), format_func=cluster_label, key="interpretation_cluster")
    subset = visible.loc[visible["Cluster"] == cluster]
    st.write(f"**{cluster_label(cluster)}** pada filter aktif")
    cards = st.columns(3)
    cards[0].metric("Jumlah record", f"{len(subset):,}")
    cards[1].metric("NIM unik", f"{subset['NIM'].nunique():,}")
    cards[2].metric("Persentase record filter", f"{len(subset)/len(visible)*100:.2f}%")
    if not len(subset):
        st.info("Cluster ini tidak memiliki record pada filter aktif.")
        return
    features = list(config.MODEL_FEATURES + config.LO_FEATURES)
    table = pd.DataFrame({"Fitur": features, "Peran": ["Input model"]*8 + ["Analisis eksternal"]*4,
                          "Rata-rata cluster (filter)": subset[features].mean().to_numpy(),
                          "Rata-rata seluruh reporting": full[features].mean().to_numpy()})
    st.dataframe(table.round(3), hide_index=True, width="stretch")
    st.write(f"Rata-rata Submit_pct pada record cluster terpilih: {subset['Submit_pct'].mean():.2f}%; Ketepatan_pct: {subset['Ketepatan_pct'].mean():.2f}%.")
    st.write(f"Rata-rata Total_LO sebagai profil eksternal: {subset['Total_LO'].mean():.2f}.")
    st.caption("Perbandingan menunjukkan profil record pada data tersedia. Nomor cluster bukan peringkat; asosiasi LO tidak menunjukkan sebab-akibat dan tidak menjadi keputusan otomatis individual.")
    st.write("Interpretasi final perlu mempertimbangkan ketimpangan ukuran cluster, dominasi Submit_pct, dan provenance Ketepatan_pct yang belum tuntas.")
