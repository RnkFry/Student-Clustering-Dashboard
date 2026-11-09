"""Prodi recommendations and filtered empirical evidence within the existing app."""

import pandas as pd
import streamlit as st

from src import config
from src.recommendation_loader import RecommendationError, load_recommendations
from src.recommendation_service import get_cluster_recommendation
from src.ui_utils import cluster_label, reporting_view


def _render_profile(profile: pd.DataFrame, global_profile: pd.DataFrame, *, percentage: bool) -> None:
    table = profile.rename(columns={"Rata-rata": "Rata-rata filter"}).copy()
    table["Rata-rata cluster global"] = global_profile["Rata-rata"].to_numpy()
    st.dataframe(table.round(3), hide_index=True, width="stretch")
    unavailable = table.loc[table["Status"] != "Tersedia", "Fitur"].tolist()
    if unavailable:
        st.warning(
            "Data tidak tersedia/lengkap: " + ", ".join(unavailable)
            + ". Dibutuhkan kolom numerik lengkap pada data/processed/clustered_data.csv. Tidak ada angka pengganti."
        )
    chart = table.melt(id_vars="Fitur", value_vars=["Rata-rata filter", "Rata-rata cluster global"],
                       var_name="Cakupan", value_name="Nilai").dropna(subset=["Nilai"])
    if chart.empty:
        return
    st.vega_lite_chart(chart, {
        "mark": "bar",
        "encoding": {
            "x": {"field": "Fitur", "type": "nominal", "sort": profile["Fitur"].tolist(), "title": None},
            "xOffset": {"field": "Cakupan"},
            "y": {"field": "Nilai", "type": "quantitative", "title": "Rata-rata (%)" if percentage else "Rata-rata nilai LO", "scale": {"zero": True}},
            "color": {"field": "Cakupan", "type": "nominal"},
            "tooltip": [{"field": "Fitur"}, {"field": "Cakupan"}, {"field": "Nilai", "format": ".3f"}],
        }, "height": 300,
    }, width="stretch")


def render() -> None:
    st.subheader("Rekomendasi Strategis Prodi")
    st.caption("Rekomendasi untuk pengelola Prodi berdasarkan label cluster final dan workbook rekomendasi.")
    try:
        mapping = load_recommendations()
        full, visible = reporting_view()
        cluster = st.selectbox("Cluster untuk rekomendasi", list(mapping), format_func=cluster_label, key="recommendation_cluster")
        result = get_cluster_recommendation(cluster, mapping, visible)
        global_result = get_cluster_recommendation(cluster, mapping, full)
    except RecommendationError as exc:
        st.error(f"Rekomendasi belum dapat ditampilkan: {exc}")
        return

    entry = result.recommendation
    st.write(f"**{cluster_label(cluster)} — {entry.profile_name}**")
    cards = st.columns(3)
    cards[0].metric("Jumlah record (filter)", f"{result.record_count:,}")
    cards[1].metric("Mahasiswa unik / NIM (filter)", f"{result.unique_student_count:,}" if result.unique_student_count is not None else "Tidak tersedia")
    cards[2].metric("Jumlah record cluster global", f"{global_result.record_count:,}")
    st.caption("Satu mahasiswa dapat memiliki beberapa record mata kuliah dan muncul pada lebih dari satu cluster. Statistik filter tidak mengubah label atau rekomendasi.")
    if result.record_count == 0:
        st.info("Cluster ini tidak memiliki record pada filter aktif. Ubah pilihan atau gunakan Reset filter untuk melihat data pendukung. Profil dan rekomendasi acuan Excel tetap ditampilkan di bawah.")
    else:
        feature_tab, lo_tab = st.tabs(["Profil delapan fitur", "Capaian LO eksternal"])
        with feature_tab:
            _render_profile(result.feature_profile, global_result.feature_profile, percentage=True)
        with lo_tab:
            st.info("avg_LO1 (LO1), avg_LO2 (LO2), avg_LO3 (LO3), dan Total_LO adalah profil eksternal; LO bukan input pembentuk cluster.")
            _render_profile(result.lo_profile, global_result.lo_profile, percentage=False)
            st.caption("Perbandingan dilakukan untuk metrik LO yang sama antara filter aktif dan cluster global, bukan sebagai persentase pencapaian terhadap target LO.")

    st.markdown("#### Karakteristik empiris — acuan Excel")
    st.text(entry.empirical_characteristics)
    st.caption("Karakteristik ini mengacu pada profil cluster global. Subset pada filter aktif dapat memiliki rata-rata berbeda.")
    st.markdown("#### Rekomendasi strategis untuk pengelola Prodi")
    st.text(entry.strategic_recommendations)
    st.caption(f"Sumber: data/reference/Rekomendasi Prodi.xlsx · Sheet1 · baris {entry.excel_row}. Teks diambil langsung dari Excel.")
    st.caption("Data pendukung: FD_pct, VBL_pct, Submit_pct, Ketepatan_pct pada profil delapan fitur; capaian LO pada profil eksternal. Angka dihitung dari reporting tersimpan. Hubungan antarprofil bersifat deskriptif, bukan bukti sebab-akibat.")
    st.caption(config.KNOWN_LIMITATIONS[0])
