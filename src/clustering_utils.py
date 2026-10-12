"""Frozen-model reporting: load -> select F8 -> transform -> predict -> export.

CLI: python -m src.clustering_utils --validate-only
     python -m src.clustering_utils --export
"""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import uuid
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.preprocessing import RobustScaler
from sklearn.utils.validation import check_is_fitted
import streamlit as st
from threadpoolctl import threadpool_limits

from src import config
from src.config import ModelContractError
from src.data_loader import (
    load_feature_engineered_data, load_raw_data, load_reporting_data,
    require_columns, sha256_file, validate_fe_schema, verify_original_file, verify_originals,
)


def validate_model_input(features: pd.DataFrame) -> np.ndarray:
    expected = list(config.MODEL_FEATURES)
    if len(expected) != 8 or len(set(expected)) != 8:
        raise ModelContractError("Config model wajib berisi tepat 8 fitur unik.")
    if set(expected).intersection(config.LO_FEATURES + config.IDENTIFIER_COLUMNS):
        raise ModelContractError("Config model tidak boleh memuat LO atau identifier.")
    if list(features.columns) != expected:
        raise ModelContractError(f"Urutan/jumlah fitur input salah. Urutan wajib: {expected}")
    if features.empty:
        raise ModelContractError("Input model kosong.")
    for column in expected:
        series = features[column]
        if not pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
            raise ModelContractError(f"Fitur {column} harus numerik, bukan teks/boolean.")
    values = features.to_numpy(dtype=float, na_value=np.nan)
    if values.ndim != 2 or values.shape[1] != 8:
        raise ModelContractError(f"Input model harus matriks dengan 8 fitur; ditemukan {values.shape}.")
    if not np.isfinite(values).all():
        bad = [expected[i] for i in np.flatnonzero(~np.isfinite(values).all(axis=0))]
        raise ModelContractError(f"Input model mengandung NaN/inf pada fitur: {', '.join(bad)}")
    return values


def prepare_model_input(df: pd.DataFrame) -> np.ndarray:
    require_columns(df, config.MODEL_FEATURES, "Input clustering")
    # Selection always follows config, regardless of the incoming DataFrame order.
    return validate_model_input(df.loc[:, list(config.MODEL_FEATURES)])


def validate_model_artifacts(scaler, model) -> None:
    if not isinstance(scaler, RobustScaler) or not isinstance(model, KMeans):
        raise ModelContractError("Kontrak memerlukan RobustScaler dan KMeans.")
    try:
        check_is_fitted(scaler, ["center_", "scale_", "n_features_in_"])
        check_is_fitted(model, ["cluster_centers_", "labels_", "n_features_in_"])
    except Exception as exc:
        raise ModelContractError(f"Model/scaler belum di-fit atau tidak lengkap: {exc}") from exc
    for name, obj, params in (
        ("Scaler", scaler, config.SCALER_PARAMS), ("Model", model, config.MODEL_PARAMS)
    ):
        if obj.n_features_in_ != 8:
            raise ModelContractError(f"{name}: n_features_in_={obj.n_features_in_}, wajib 8.")
        names = getattr(obj, "feature_names_in_", None)
        if names is not None and list(names) != list(config.MODEL_FEATURES):
            raise ModelContractError(f"{name}: nama/urutan fitur berbeda dari config.")
        for key, expected in params.items():
            if obj.get_params().get(key) != expected:
                raise ModelContractError(f"{name}: parameter {key} berbeda dari audit; wajib {expected}.")
    if model.cluster_centers_.shape != (4, 8) or not np.isfinite(model.cluster_centers_).all():
        raise ModelContractError("Centroid model harus finite dengan shape (4, 8).")
    if scaler.center_.shape != (8,) or scaler.scale_.shape != (8,):
        raise ModelContractError("Parameter scaler harus memiliki tepat 8 elemen.")
    if not np.isfinite(scaler.center_).all() or not np.isfinite(scaler.scale_).all() or (scaler.scale_ <= 0).any():
        raise ModelContractError("Parameter scaler mengandung nilai nonfinite atau skala <= 0.")


@st.cache_resource(show_spinner=False)
def _load_artifacts(model_path: str, model_digest: str, scaler_path: str, scaler_digest: str, sklearn_version: str):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", InconsistentVersionWarning)
            scaler = joblib.load(scaler_path)
            model = joblib.load(model_path)
        validate_model_artifacts(scaler, model)
        return scaler, model
    except ModelContractError:
        raise
    except Exception as exc:
        raise ModelContractError(f"Gagal load model/scaler: {type(exc).__name__}: {exc}") from exc


def load_model_and_scaler():
    version = importlib.metadata.version("scikit-learn")
    if version != config.EXPECTED_SKLEARN_VERSION:
        raise ModelContractError(
            f"scikit-learn {version} berbeda dari kontrak {config.EXPECTED_SKLEARN_VERSION}. "
            "Gunakan environment audit atau requirements.txt."
        )
    model_digest = verify_original_file(config.MODEL_PATH)
    scaler_digest = verify_original_file(config.SCALER_PATH)
    return _load_artifacts(str(config.MODEL_PATH), model_digest, str(config.SCALER_PATH), scaler_digest, version)


def predict_clusters(df: pd.DataFrame, scaler, model) -> np.ndarray:
    values = prepare_model_input(df)
    validate_model_artifacts(scaler, model)
    try:
        # Artifact caches hold fitted objects. Never call fit/fit_transform/fit_predict.
        with threadpool_limits(limits=2):
            transformed = scaler.transform(values)
            if transformed.shape != values.shape or not np.isfinite(transformed).all():
                raise ModelContractError("Hasil scaler.transform() tidak finite atau shape berubah.")
            labels = model.predict(transformed)
    except ModelContractError:
        raise
    except Exception as exc:
        raise ModelContractError(f"Transform/predict gagal: {exc}") from exc
    if labels.shape != (len(df),) or not np.isin(labels, range(4)).all():
        raise ModelContractError("Prediksi harus satu label Cluster 0..3 untuk setiap record.")
    return labels.astype(np.int64)


def build_clustered_dataset() -> pd.DataFrame:
    fe = load_feature_engineered_data()
    scaler, model = load_model_and_scaler()
    labels = predict_clusters(fe, scaler, model)
    if not np.array_equal(labels, model.labels_):
        raise ModelContractError("Prediksi berbeda dari labels_ model tersimpan pada urutan FE asli.")
    counts = {int(k): int(v) for k, v in pd.Series(labels).value_counts().items()}
    if counts != config.EXPECTED_CLUSTER_COUNTS:
        raise ModelContractError(f"Distribusi cluster berbeda dari audit: {counts}")
    result = fe.copy(deep=True)
    result[config.CLUSTER_COLUMN] = labels
    validate_fe_schema(result, with_cluster=True)
    return result


def build_cluster_summary(clustered_df: pd.DataFrame) -> pd.DataFrame:
    validate_fe_schema(clustered_df, with_cluster=True)
    groups = clustered_df.groupby(config.CLUSTER_COLUMN, sort=True)
    summary = groups.size().rename("Record_Count").to_frame()
    summary["Record_Percentage"] = summary["Record_Count"] / len(clustered_df) * 100
    summary["Unique_NIM_Count"] = groups["NIM"].nunique()
    means = groups[list(config.MODEL_FEATURES + config.LO_FEATURES)].mean().add_prefix("Mean_")
    return summary.join(means).reset_index()


def validate_project() -> tuple[pd.DataFrame, dict]:
    before = verify_originals()
    raw = load_raw_data()
    fe = load_feature_engineered_data()
    if not raw[list(config.IDENTIFIER_COLUMNS)].equals(fe[list(config.IDENTIFIER_COLUMNS)]):
        raise ModelContractError("Identifier atau urutan record raw dan FE berbeda.")
    if fe["NIM"].nunique() != config.MODEL_METADATA["unique_nim_count"]:
        raise ModelContractError("Jumlah NIM unik berbeda dari audit (583).")
    clustered = build_clustered_dataset()
    if verify_originals() != before:
        raise ModelContractError("File sumber berubah selama validasi.")
    details = {
        "contract_version": config.CONTRACT_VERSION,
        "record_count": len(clustered),
        "unique_nim_count": int(clustered["NIM"].nunique()),
        "cluster_counts": config.EXPECTED_CLUSTER_COUNTS,
        "labels_match_saved_model": True,
        "original_files_unchanged": True,
        "known_limitations": list(config.KNOWN_LIMITATIONS),
        "project_plan_changed_since_audit": sha256_file(config.PROJECT_PLAN_PATH) != config.AUDITED_PROJECT_PLAN_SHA256,
    }
    # Existing reporting is also validated; errors must not be silently ignored.
    targets = (config.CLUSTERED_DATA_PATH, config.CLUSTER_SUMMARY_PATH, config.REPORTING_MANIFEST_PATH)
    if any(path.exists() for path in targets):
        saved = load_reporting_data()
        try:
            pd.testing.assert_frame_equal(saved, clustered, check_exact=False, rtol=1e-12, atol=1e-12)
            saved_summary = pd.read_csv(config.CLUSTER_SUMMARY_PATH)
            pd.testing.assert_frame_equal(saved_summary, build_cluster_summary(clustered), check_exact=False, rtol=1e-12, atol=1e-12)
        except AssertionError as exc:
            raise ModelContractError(f"Dataset/summary reporting berbeda dari prediksi tervalidasi: {exc}") from exc
        details["existing_reporting_valid"] = True
    return clustered, details


def _publish_reporting_payloads(payloads: dict[Path, bytes]) -> None:
    """Stage with the output folder's inherited ACL, then publish manifest last.

    Python 3.13 on Windows makes TemporaryDirectory (mode 0700) owner-only.
    Renaming files from it preserves that ACL and prevents the normal desktop
    account from reading exports made by a sandbox account.
    """
    output_dir = config.PROCESSED_DIR.resolve()
    if any(path.parent.resolve() != output_dir for path in payloads):
        raise ModelContractError("Path output staging wajib berada di data/processed/.")
    staging = output_dir / f".reporting-{uuid.uuid4().hex}"
    staging.mkdir(mode=0o777)  # Normal directory creation inherits the parent's Windows ACL.
    staged_paths = [staging / path.name for path in payloads]
    try:
        for path, payload in payloads.items():
            (staging / path.name).write_bytes(payload)
        for path in payloads:
            os.replace(staging / path.name, path)
    finally:
        # Clean only the exact files this invocation created, without recursive deletion.
        for path in staged_paths:
            path.unlink(missing_ok=True)
        staging.rmdir()


def save_reporting_artifacts(clustered_df: pd.DataFrame, *, overwrite: bool = False) -> dict[str, Path]:
    sources = verify_originals()
    validate_fe_schema(clustered_df, with_cluster=True)
    expected = build_clustered_dataset()
    try:
        pd.testing.assert_frame_equal(clustered_df, expected)
    except AssertionError as exc:
        raise ModelContractError("Export ditolak: dataset tidak sama dengan hasil prediksi FE asli.") from exc
    # Reject redirected directories, including a symlink/junction outside this location.
    if config.PROCESSED_DIR.resolve() != config.DATA_DIR.resolve() / "processed":
        raise ModelContractError("Path output wajib data/processed/ tanpa pengalihan direktori.")
    targets = {
        "clustered_data": config.CLUSTERED_DATA_PATH,
        "cluster_summary": config.CLUSTER_SUMMARY_PATH,
        "manifest": config.REPORTING_MANIFEST_PATH,
    }
    for path in targets.values():
        if path.parent.resolve() != config.PROCESSED_DIR.resolve() or path.is_symlink():
            raise ModelContractError(f"Path output tidak aman: {path}")
    existing = [path.name for path in targets.values() if path.exists()]
    if existing and not overwrite:
        raise ModelContractError(
            f"Artefak turunan sudah tersedia: {', '.join(existing)}. "
            "Gunakan --validate-only atau --export --overwrite untuk mengganti hanya artefak turunan."
        )
    summary = build_cluster_summary(clustered_df)
    # Identifier strings are retained in CSV. Excel may still infer numeric IDs on manual open.
    payloads = {
        targets["clustered_data"]: clustered_df.to_csv(index=False, lineterminator="\n").encode("utf-8-sig"),
        targets["cluster_summary"]: summary.to_csv(index=False, lineterminator="\n").encode("utf-8-sig"),
    }
    manifest = {
        "contract_version": config.CONTRACT_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "reporting_from_audited_FE_using_frozen_model",
        "audit_report": config.AUDIT_REPORT_PATH.name,
        "model_metadata": config.MODEL_METADATA,
        "model_features": list(config.MODEL_FEATURES),
        "external_profile_features": list(config.LO_FEATURES),
        "identifier_columns": list(config.IDENTIFIER_COLUMNS),
        "row_count": len(clustered_df),
        "cluster_counts": config.EXPECTED_CLUSTER_COUNTS,
        "source_sha256": sources,
        "documentation_sha256": {
            path.name: sha256_file(path)
            for path in (config.PROJECT_PLAN_PATH, config.AUDIT_REPORT_PATH, config.AUDIT_MANIFEST_PATH)
        },
        "project_plan_changed_since_audit": sha256_file(config.PROJECT_PLAN_PATH) != config.AUDITED_PROJECT_PLAN_SHA256,
        "output_sha256": {path.name: hashlib.sha256(data).hexdigest() for path, data in payloads.items()},
        "known_limitations": list(config.KNOWN_LIMITATIONS),
        "python_packages": {
            name: importlib.metadata.version(name)
            for name in ("pandas", "numpy", "scikit-learn", "scipy", "joblib", "openpyxl", "streamlit")
        },
    }
    payloads[targets["manifest"]] = json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8")
    if verify_originals() != sources:
        raise ModelContractError("File sumber berubah sebelum export.")
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    # Stage complete files; replace manifest last so incomplete batches fail validation.
    _publish_reporting_payloads(payloads)
    verify_originals()
    load_reporting_data()
    return targets


def main() -> int:
    parser = argparse.ArgumentParser(description="Validasi kontrak audit dan export reporting tanpa retraining.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--validate-only", action="store_true", help="Validasi tanpa menulis artefak (default).")
    mode.add_argument("--export", action="store_true", help="Tulis artefak baru ke data/processed/.")
    parser.add_argument("--overwrite", action="store_true", help="Ganti hanya artefak reporting turunan.")
    args = parser.parse_args()
    if args.overwrite and not args.export:
        parser.error("--overwrite hanya berlaku bersama --export")
    try:
        clustered, details = validate_project()
        if args.export:
            paths = save_reporting_artifacts(clustered, overwrite=args.overwrite)
            details["saved_artifacts"] = {name: str(path) for name, path in paths.items()}
        print(json.dumps(details, indent=2, ensure_ascii=False))
        return 0
    except (ModelContractError, OSError) as exc:
        print(f"VALIDASI GAGAL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
