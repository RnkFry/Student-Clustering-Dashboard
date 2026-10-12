"""Explicit contract from AUDIT_AWAL_PROJECT.md; paths are independent of cwd."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DATA_PATH = DATA_DIR / "raw_data.xlsx"
FE_DATA_PATH = DATA_DIR / "feature_engineered_data.xlsx"
MODEL_PATH = MODELS_DIR / "clustering_model.pkl"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks/KMeans_Student_Clustering_8F_Dataset_V3.ipynb"
AUDIT_REPORT_PATH = PROJECT_ROOT / "AUDIT_AWAL_PROJECT.md"
AUDIT_MANIFEST_PATH = PROJECT_ROOT / "audit/artifact_manifest.json"
PROJECT_PLAN_PATH = PROJECT_ROOT / "PROJECT_PLAN_DASHBOARD_STREAMLIT_BINUS_REVISED.md"
AUDITED_PROJECT_PLAN_SHA256 = "3cf670239a72c5774461a3faaf70b56e8b00e655704ffb32ed7285e30f730268"
CLUSTERED_DATA_PATH = PROCESSED_DIR / "clustered_data.csv"
CLUSTER_SUMMARY_PATH = PROCESSED_DIR / "cluster_summary.csv"
REPORTING_MANIFEST_PATH = PROCESSED_DIR / "reporting_manifest.json"
RAW_SHEET_NAME = "Sheet1"
FE_SHEET_NAME = "Fitur_Clustering"
CLUSTER_COLUMN = "Cluster"
CONTRACT_VERSION = "F8-ROBUST-K4-v1"
EXPECTED_SKLEARN_VERSION = "1.9.0"

# Immutable and ordered: LO and identifiers must never enter the model matrix.
MODEL_FEATURES = (
    "Course_pct", "Dosen_pct", "FD_pct", "PPT_pct", "LN_pct", "VBL_pct",
    "Submit_pct", "Ketepatan_pct",
)
LO_FEATURES = ("avg_LO1", "avg_LO2", "avg_LO3", "Total_LO")
IDENTIFIER_COLUMNS = (
    "Kode_Periode", "Kode Kelas", "Kode Dosen", "Kode Mata kuliah", "Mata kuliah", "NIM",
)
RECORD_KEY_COLUMNS = ("Kode_Periode", "Kode Mata kuliah", "Kode Kelas", "NIM")
FE_COLUMNS = IDENTIFIER_COLUMNS + MODEL_FEATURES + LO_FEATURES
IDENTIFIER_DTYPES = {column: "string" for column in IDENTIFIER_COLUMNS}
EXPECTED_CLUSTER_COUNTS = {0: 4820, 1: 60, 2: 559, 3: 286}
MODEL_METADATA = {
    "audit_date": "2026-10-11",
    "model": "K-Means",
    "scaler": "RobustScaler",
    "feature_case": "F8",
    "n_features": 8,
    "n_clusters": 4,
    "k_selection": "MANUAL_OVERRIDE",
    "random_state": 42,
    "n_init": 30,
    "max_iter": 500,
    "record_count": 5725,
    "unique_nim_count": 583,
    "silhouette": 0.8419545975733478,
    "davies_bouldin": 0.34071568987823875,
    "calinski_harabasz": 36864.558668704165,
    "inertia": 42983.126580796845,
    "sklearn_version": EXPECTED_SKLEARN_VERSION,
}
MODEL_PARAMS = {
    "n_clusters": 4, "random_state": 42, "n_init": 30, "max_iter": 500,
    "init": "k-means++", "algorithm": "lloyd", "tol": 0.0001, "copy_x": True,
}
SCALER_PARAMS = {
    "quantile_range": (25.0, 75.0), "with_centering": True,
    "with_scaling": True, "unit_variance": False,
}
KNOWN_LIMITATIONS = (
    "Ketepatan_pct belum konsisten dengan kandidat rumus timestamp/deadline raw "
    "pada 1.886 baris. Reporting memakai nilai FE tersimpan; provenance raw ke FE belum tuntas.",
    "Submit_pct memiliki IQR nol; skala fitur ini berpotensi mendominasi jarak clustering.",
    "K=4 dipilih manual. Nomor cluster tidak menyatakan urutan kualitas mahasiswa.",
)

# Pin audited content as well as schema. A replacement requires a new audit/contract.
ORIGINAL_SHA256 = {
    "data/raw_data.xlsx": "704cd4a76d5a181e1d4cb4762c301b4e93654b39c6682571d1df6f990eb95ea0",
    "data/feature_engineered_data.xlsx": "1adf7131beb78d8d83abbf57b105224fe387c3a2b03a24e5ec08c46f8b6869f4",
    "models/clustering_model.pkl": "66e59f24b6194ed442ea0493e00ca3a126ad0e75fd43ce9923dae4269abec629",
    "models/scaler.pkl": "c97984b738a9e7c2e7d86178c7bae9b3dfa62376c4ffa208f6756bdb8b5f00ea",
    "notebooks/KMeans_Student_Clustering_8F_Dataset_V3.ipynb": "6ee793dccc8e8eab3e230b2d3bcc4a63fca30bc97489cd38e6c61c43e54a6d2d",
}


class ModelContractError(ValueError):
    """An artifact or schema does not satisfy the audited reporting contract."""
