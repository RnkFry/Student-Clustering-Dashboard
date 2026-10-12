import pandas as pd
import streamlit as st

from src import config
from src.clustering_utils import load_model_and_scaler


def render() -> None:
    st.subheader("Modeling Pipeline")
    st.code("FE tersimpan\n  ↓ Pilih F8 sesuai urutan kontrak\nRobustScaler.transform()\n  ↓\nKMeans.predict()\n  ↓\nReporting tersimpan\n  ↓ Filter tampilan\nAnalisis & download", language=None)
    st.write("Raw data dipakai untuk pemahaman dan EDA. Rekonstruksi raw → FE belum tersedia; tahap reporting menggunakan FE yang sudah cocok dengan artefak model.")
    scaler, model = load_model_and_scaler()
    metadata = [
        ("Model", "K-Means"), ("Scaler", "RobustScaler"), ("Jumlah fitur", 8),
        ("Jumlah cluster", 4), ("Pemilihan K", "Manual override"),
        ("Random state", 42), ("n_init", 30), ("max_iter", 500),
        ("scikit-learn", config.EXPECTED_SKLEARN_VERSION),
        ("Silhouette final", f"{config.MODEL_METADATA['silhouette']:.5f}"),
        ("Davies-Bouldin", f"{config.MODEL_METADATA['davies_bouldin']:.5f}"),
        ("Calinski-Harabasz", f"{config.MODEL_METADATA['calinski_harabasz']:.2f}"),
        ("Inertia", f"{config.MODEL_METADATA['inertia']:.2f}"),
    ]
    st.dataframe(pd.DataFrame([(k, str(v)) for k, v in metadata], columns=["Parameter", "Nilai"]), hide_index=True, width="stretch")
    st.caption("Metrik untuk model final pada seluruh data audit. K=4 bukan hasil maksimum silhouette otomatis.")
    with st.expander("Urutan input dan parameter scaler"):
        st.dataframe(pd.DataFrame({"Fitur": config.MODEL_FEATURES, "Center (median)": scaler.center_, "Scale": scaler.scale_}), hide_index=True, width="stretch")
        st.write("Submit_pct memiliki IQR nol dan scale=1; geometri clustering perlu diinterpretasikan dengan konteks ini.")
    with st.expander("Centroid global pada skala asli"):
        centers = pd.DataFrame(scaler.inverse_transform(model.cluster_centers_), columns=config.MODEL_FEATURES)
        centers.index = [f"Cluster {i}" for i in range(4)]
        st.dataframe(centers.round(3), width="stretch")
    st.info("Filter hanya mengubah tampilan. Halaman ini memuat artefak fitted melalui cache; tidak ada training ulang atau fit ulang scaler.")
