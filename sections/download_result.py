from io import BytesIO
import json

import pandas as pd
import streamlit as st

from src import config
from src.data_loader import load_reporting_manifest
from src.eda_utils import summarize_clusters
from src.ui_utils import current_filters, render_dataset_metrics, reporting_view, require_visible_records


@st.cache_data(show_spinner=False)
def export_payloads(visible: pd.DataFrame, include_identifiers: bool) -> dict[str, bytes]:
    data = visible.copy()
    summary = summarize_clusters(visible)
    if not include_identifiers:
        data = data.drop(columns=list(config.IDENTIFIER_COLUMNS))
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        data.to_excel(writer, sheet_name="Reporting", index=False)
        summary.to_excel(writer, sheet_name="Cluster_Summary", index=False)
    return {
        "dataset": data.to_csv(index=False, lineterminator="\n").encode("utf-8-sig"),
        "summary": summary.to_csv(index=False, lineterminator="\n").encode("utf-8-sig"),
        "excel": buffer.getvalue(),
    }


def render() -> None:
    st.subheader("Download Result")
    _, visible = reporting_view()
    render_dataset_metrics(visible)
    st.write("Download mengikuti filter aktif dan memakai label cluster tersimpan.")
    if not require_visible_records(visible):
        return
    include = st.checkbox("Sertakan kolom identifier", value=False, key="download_include_identifiers")
    st.caption("Default menghapus enam identifier dari dataset unduhan. Baris tetap memuat aktivitas dan nilai akademik; penghapusan identifier saja belum menjamin anonimisasi penuh.")
    payloads = export_payloads(visible, include)
    metadata = {
        "provenance": load_reporting_manifest(), "export_scope": "filtered_reporting",
        "filters": current_filters(), "record_count": len(visible),
        "unique_nim_count": int(visible["NIM"].nunique()), "identifiers_included": include,
        "summary_nim_counts": "NIM dapat berada pada beberapa cluster; jangan menjumlahkan NIM unik per cluster.",
    }
    st.download_button("Download dataset CSV", payloads["dataset"], "reporting_filtered.csv", "text/csv", key="download_csv", on_click="ignore")
    st.download_button("Download summary CSV", payloads["summary"], "cluster_summary_filtered.csv", "text/csv", key="download_summary", on_click="ignore")
    st.download_button("Download Excel (dataset + summary)", payloads["excel"], "reporting_filtered.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="download_excel", on_click="ignore")
    st.download_button("Download provenance JSON", json.dumps(metadata, indent=2, ensure_ascii=False).encode("utf-8"), "reporting_export_provenance.json", "application/json", key="download_provenance", on_click="ignore")
    st.caption("Provenance mencatat hash sumber reporting dan pilihan filter. Download dibentuk dalam memori; file sumber dan reporting lokal tetap utuh.")
