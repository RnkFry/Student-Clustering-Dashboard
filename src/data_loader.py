"""Content-keyed Streamlit caches and strict loaders for original/derived data."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from src import config
from src.config import ModelContractError


def sha256_file(path: Path) -> str:
    if not path.is_file():
        raise ModelContractError(f"File tidak ditemukan: {path}")
    try:
        with path.open("rb") as handle:
            return hashlib.file_digest(handle, "sha256").hexdigest()
    except PermissionError as exc:
        raise ModelContractError(
            f"Izin baca ditolak untuk {path}. Periksa izin Windows akun yang menjalankan Streamlit; "
            "lihat petunjuk Permission denied di README.md."
        ) from exc


def verify_original_file(path: Path) -> str:
    path = path.resolve()
    try:
        relative = path.relative_to(config.PROJECT_ROOT).as_posix()
    except ValueError as exc:
        raise ModelContractError(f"Path di luar kontrak proyek: {path}") from exc
    expected = config.ORIGINAL_SHA256.get(relative)
    if expected is None:
        raise ModelContractError(f"File tidak terdaftar dalam kontrak audit: {relative}")
    digest = sha256_file(path)
    if digest != expected:
        raise ModelContractError(
            f"SHA-256 {relative} berbeda dari audit. Hentikan reporting dan audit ulang artefak."
        )
    return digest


def verify_originals() -> dict[str, str]:
    return {
        relative: verify_original_file(config.PROJECT_ROOT / relative)
        for relative in config.ORIGINAL_SHA256
    }


def require_columns(df: pd.DataFrame, required: tuple[str, ...], name: str) -> None:
    if df.columns.has_duplicates:
        raise ModelContractError(f"{name}: nama kolom duplikat tidak diizinkan.")
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ModelContractError(f"{name}: kolom wajib tidak tersedia: {', '.join(missing)}")
    if df.empty:
        raise ModelContractError(f"{name}: dataset kosong.")


def validate_fe_schema(df: pd.DataFrame, *, with_cluster: bool = False) -> None:
    required = config.FE_COLUMNS + ((config.CLUSTER_COLUMN,) if with_cluster else ())
    require_columns(df, required, "Dataset FE/reporting")
    if list(df.columns) != list(required):
        raise ModelContractError(
            "Dataset FE/reporting: nama atau urutan kolom berbeda dari kontrak. "
            f"Urutan wajib: {list(required)}"
        )
    if df[list(config.IDENTIFIER_COLUMNS)].isna().any().any():
        raise ModelContractError("Dataset FE/reporting: identifier mengandung missing value.")
    if df.duplicated(list(config.RECORD_KEY_COLUMNS)).any():
        raise ModelContractError("Dataset FE/reporting: kunci record mahasiswa duplikat.")
    for column in config.MODEL_FEATURES + config.LO_FEATURES:
        values = df[column]
        if not pd.api.types.is_numeric_dtype(values) or pd.api.types.is_bool_dtype(values):
            raise ModelContractError(f"Dataset FE/reporting: {column} harus numerik, bukan teks/boolean.")
        if not np.isfinite(values.to_numpy(dtype=float, na_value=np.nan)).all():
            raise ModelContractError(f"Dataset FE/reporting: {column} mengandung NaN/inf atau missing value.")
    if with_cluster:
        values = df[config.CLUSTER_COLUMN]
        if not pd.api.types.is_integer_dtype(values) or not values.isin(range(4)).all():
            raise ModelContractError("Dataset reporting: Cluster wajib integer 0, 1, 2, atau 3.")


@st.cache_data(show_spinner=False)
def _read_excel(path: str, content_sha256: str, sheet_name: str) -> pd.DataFrame:
    # content_sha256 is deliberately a cache argument, not an ignored underscore argument.
    try:
        return pd.read_excel(
            path, sheet_name=sheet_name, engine="openpyxl", dtype=config.IDENTIFIER_DTYPES
        )
    except Exception as exc:
        raise ModelContractError(f"Gagal membaca Excel {path}, sheet {sheet_name}: {exc}") from exc


def load_raw_data() -> pd.DataFrame:
    digest = verify_original_file(config.RAW_DATA_PATH)
    df = _read_excel(str(config.RAW_DATA_PATH), digest, config.RAW_SHEET_NAME)
    require_columns(df, config.IDENTIFIER_COLUMNS, "Raw data")
    if df.shape != (5725, 103):
        raise ModelContractError(f"Raw data: shape {df.shape} berbeda dari audit (5725, 103).")
    return df


def load_feature_engineered_data() -> pd.DataFrame:
    digest = verify_original_file(config.FE_DATA_PATH)
    df = _read_excel(str(config.FE_DATA_PATH), digest, config.FE_SHEET_NAME)
    validate_fe_schema(df)
    if len(df) != config.MODEL_METADATA["record_count"]:
        raise ModelContractError("FE: jumlah record berbeda dari audit (5725).")
    return df


@st.cache_data(show_spinner=False)
def _read_csv(path: str, content_sha256: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path, dtype=config.IDENTIFIER_DTYPES)
    except Exception as exc:
        raise ModelContractError(f"Gagal membaca dataset reporting {path}: {exc}") from exc


def load_reporting_manifest() -> dict:
    """Validate the source contract and both reporting files before returning provenance."""
    sources = verify_originals()
    if not config.REPORTING_MANIFEST_PATH.is_file():
        raise ModelContractError(
            "Artefak reporting belum tersedia. Jalankan: python -m src.clustering_utils --export"
        )
    try:
        manifest = json.loads(config.REPORTING_MANIFEST_PATH.read_text(encoding="utf-8"))
        if manifest["contract_version"] != config.CONTRACT_VERSION or manifest["source_sha256"] != sources:
            raise ModelContractError("Manifest reporting berbeda dari kontrak/sumber audit.")
        if manifest["model_features"] != list(config.MODEL_FEATURES):
            raise ModelContractError("Manifest reporting: urutan fitur model berbeda dari config.")
        for path in (config.CLUSTERED_DATA_PATH, config.CLUSTER_SUMMARY_PATH):
            if sha256_file(path) != manifest["output_sha256"][path.name]:
                raise ModelContractError(f"Artefak reporting berubah atau tidak lengkap: {path.name}")
    except PermissionError as exc:
        raise ModelContractError(
            f"Izin baca ditolak untuk {exc.filename or config.REPORTING_MANIFEST_PATH}. "
            "Periksa izin Windows akun yang menjalankan Streamlit; "
            "lihat petunjuk Permission denied di README.md."
        ) from exc
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ModelContractError(f"Manifest reporting tidak valid: {exc}") from exc
    return manifest


def load_reporting_data() -> pd.DataFrame:
    manifest = load_reporting_manifest()
    digest = manifest["output_sha256"][config.CLUSTERED_DATA_PATH.name]
    df = _read_csv(str(config.CLUSTERED_DATA_PATH), digest)
    validate_fe_schema(df, with_cluster=True)
    if len(df) != config.MODEL_METADATA["record_count"]:
        raise ModelContractError("Reporting: jumlah record berbeda dari kontrak audit.")
    if df[config.CLUSTER_COLUMN].value_counts().to_dict() != config.EXPECTED_CLUSTER_COUNTS:
        raise ModelContractError("Reporting: distribusi label cluster berbeda dari audit.")
    return df
