"""Read-only artifact audit; writes only audit/artifact_manifest.json."""

import ast
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import sys
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from threadpoolctl import threadpool_limits


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks/KMeans_Student_Clustering_8F_Dataset_V3.ipynb"
ORIGINALS = [
    ROOT / "PROJECT_PLAN_DASHBOARD_STREAMLIT_BINUS_REVISED.md",
    ROOT / "data/raw_data.xlsx",
    ROOT / "data/feature_engineered_data.xlsx",
    ROOT / "models/clustering_model.pkl",
    ROOT / "models/scaler.pkl",
    NOTEBOOK,
]


def hashes():
    return {
        str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in ORIGINALS
    }


def native(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(type(value).__name__)


def describe(df):
    return {
        "shape": list(df.shape),
        "columns": list(df.columns),
        "dtypes": {c: str(d) for c, d in df.dtypes.items()},
        "missing_by_column": {c: int(v) for c, v in df.isna().sum().items()},
        "duplicate_rows": int(df.duplicated().sum()),
        "unique_nim": int(df["NIM"].nunique()),
        "unique_class_codes": int(df["Kode Kelas"].nunique()),
        "unique_course_codes": int(df["Kode Mata kuliah"].nunique()),
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    before = hashes()
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    config = {}
    # Extract literal configuration only; do not execute notebook cells.
    for cell_index in (2, 4, 6):
        tree = ast.parse("".join(nb["cells"][cell_index]["source"]))
        for node in tree.body:
            if isinstance(node, ast.Assign):
                try:
                    value = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    continue
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        config[target.id] = value
    features = config["FEATURE_CASES"][config["ACTIVE_CASE"]]
    packages = [
        "pandas", "numpy", "openpyxl", "scikit-learn", "scipy", "joblib",
        "threadpoolctl", "streamlit", "plotly", "matplotlib", "seaborn",
        "ipython", "ipykernel", "statsmodels", "umap-learn", "numba", "pynndescent",
    ]
    versions = {}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    manifest = {
        "audit_date": "2026-10-11",
        "python": sys.version,
        "executable": sys.executable,
        "packages": versions,
        "notebook": str(NOTEBOOK.relative_to(ROOT)).replace("\\", "/"),
        "notebook_config": config,
        "model_features_in_order": features,
        "notebook_error_outputs": [
            {"cell": i, "ename": out.get("ename"), "evalue": out.get("evalue")}
            for i, cell in enumerate(nb["cells"])
            for out in cell.get("outputs", [])
            if out.get("output_type") == "error"
        ],
    }
    raw_path = ROOT / "data/raw_data.xlsx"
    fe_path = ROOT / "data/feature_engineered_data.xlsx"
    raw_book = pd.ExcelFile(raw_path, engine="openpyxl")
    fe_book = pd.ExcelFile(fe_path, engine="openpyxl")
    raw = pd.read_excel(raw_book, sheet_name="Sheet1")
    fe = pd.read_excel(fe_book, sheet_name="Fitur_Clustering")
    manifest["raw"] = {"sheets": raw_book.sheet_names, **describe(raw)}
    manifest["feature_engineered"] = {"sheets": fe_book.sheet_names, **describe(fe)}
    raw_book.close()
    fe_book.close()
    identifiers = config["ID_COLUMNS"]
    keys = ["Kode_Periode", "Kode Mata kuliah", "Kode Kelas", "NIM"]
    manifest["alignment"] = {
        "id_columns": identifiers,
        "all_ids_equal_in_row_order": raw[identifiers].equals(fe[identifiers]),
        "id_mismatches_by_column": {
            c: int((raw[c] != fe[c]).sum()) for c in identifiers
        },
        "candidate_grain_keys": keys,
        "raw_duplicate_keys": int(raw.duplicated(keys).sum()),
        "fe_duplicate_keys": int(fe.duplicated(keys).sum()),
        "unique_class_course_period": int(fe[keys[:3]].drop_duplicates().shape[0]),
    }
    X = fe[features].to_numpy(dtype=float)
    manifest["feature_quality"] = {
        "all_numeric": all(pd.api.types.is_numeric_dtype(fe[c]) for c in features),
        "all_finite": bool(np.isfinite(X).all()),
        "outside_0_100": {c: int(((fe[c] < 0) | (fe[c] > 100)).sum()) for c in features},
        "total_lo_sum_max_abs_diff": float(
            (fe["Total_LO"] - fe[["avg_LO1", "avg_LO2", "avg_LO3"]].sum(axis=1)).abs().max()
        ),
        "cluster_column_present": "Cluster" in fe.columns,
    }
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model = joblib.load(ROOT / "models/clustering_model.pkl")
        scaler = joblib.load(ROOT / "models/scaler.pkl")
        with threadpool_limits(limits=2):
            scaled = scaler.transform(X)
            predicted = model.predict(scaled)
            metrics = {
                "silhouette": float(silhouette_score(scaled, predicted)),
                "davies_bouldin": float(davies_bouldin_score(scaled, predicted)),
                "calinski_harabasz": float(calinski_harabasz_score(scaled, predicted)),
                "recomputed_inertia": float(((scaled - model.cluster_centers_[predicted]) ** 2).sum()),
                "saved_inertia": float(model.inertia_),
            }
    manifest["load_warnings"] = [str(w.message) for w in caught]
    for name, obj in (("model", model), ("scaler", scaler)):
        artifact_path = ROOT / "models" / ("clustering_model.pkl" if name == "model" else "scaler.pkl")
        version_match = re.search(rb"_sklearn_version.{0,8}?(\d+\.\d+\.\d+)", artifact_path.read_bytes())
        manifest[name] = {
            "load_success": True,
            "class": f"{type(obj).__module__}.{type(obj).__name__}",
            "params": obj.get_params(),
            "n_features_in": int(obj.n_features_in_),
            "feature_names_in": getattr(obj, "feature_names_in_", None),
            "serialized_sklearn_version": version_match.group(1).decode() if version_match else None,
        }
    manifest["model"].update({
        "cluster_centers_shape": list(model.cluster_centers_.shape),
        "saved_labels_count": len(model.labels_),
        "n_iter": int(model.n_iter_),
    })
    q1, median, q3 = np.quantile(X, [0.25, 0.5, 0.75], axis=0)
    iqr = q3 - q1
    expected_scale = iqr.copy()
    expected_scale[expected_scale < 10 * np.finfo(expected_scale.dtype).eps] = 1
    manifest["scaler"].update({
        "center": scaler.center_,
        "scale": scaler.scale_,
        "dataset_iqr": iqr,
        "zero_iqr_features": [features[i] for i in np.flatnonzero(np.isclose(iqr, 0))],
        "center_matches_dataset_median": bool(np.allclose(scaler.center_, median)),
        "scale_matches_dataset_iqr_with_zero_handling": bool(np.allclose(scaler.scale_, expected_scale)),
        "median_max_abs_diff": float(np.max(np.abs(scaler.center_ - median))),
        "scale_max_abs_diff": float(np.max(np.abs(scaler.scale_ - expected_scale))),
        "transformed_std_ddof1": scaled.std(axis=0, ddof=1),
        "transformed_min": scaled.min(axis=0),
        "transformed_max": scaled.max(axis=0),
    })
    empirical_centers = np.array([scaled[predicted == c].mean(axis=0) for c in range(model.n_clusters)])
    manifest["predictions"] = {
        "shape": list(scaled.shape),
        "all_transformed_finite": bool(np.isfinite(scaled).all()),
        "exact_match_saved_labels_in_row_order": bool(np.array_equal(predicted, model.labels_)),
        "mismatch_count": int((predicted != model.labels_).sum()),
        "cluster_sizes": {str(c): int((predicted == c).sum()) for c in range(model.n_clusters)},
        "centroid_max_abs_diff_from_empirical_means": float(np.abs(empirical_centers - model.cluster_centers_).max()),
        "metrics": metrics,
        "mean_features_per_cluster": fe.assign(Cluster=predicted).groupby("Cluster")[features].mean().to_dict(orient="index"),
    }
    # Compare simple FE candidates with raw data, explicitly as hypotheses.
    candidates = {}
    for prefix in ("FD", "PPT", "LN", "VBL"):
        cols = [f"{prefix}{i}" for i in range(1, 11)]
        values = raw[cols]
        candidates[prefix + "_pct"] = {
            "candidate_formula": "mean of 10 raw columns * 100",
            "raw_unique_values": sorted(pd.unique(values.to_numpy().ravel()).tolist(), key=str),
            "max_abs_diff": float((values.mean(axis=1) * 100 - fe[prefix + "_pct"]).abs().max()),
        }
    tasks = ["TP1", "TP2", "TK1", "TK2", "TK3", "TK4", "Quiz1", "Quiz2", "Final_Exam"]
    for lo in (1, 2, 3):
        cols = [f"{t}_LO{lo}" for t in tasks]
        candidates[f"avg_LO{lo}"] = {
            "candidate_formula": "mean of 9 raw assessment LO columns",
            "max_abs_diff": float((raw[cols].mean(axis=1) - fe[f"avg_LO{lo}"]).abs().max()),
        }
    submission_tasks = tasks[:6]
    timestamps = raw[[f"Timestamp_{t}" for t in submission_tasks]]
    submitted = timestamps.notna().sum(axis=1) / len(submission_tasks) * 100
    on_time_count = sum(
        (raw[f"Timestamp_{t}"] <= raw[f"Deadline_{t}"]).astype(int)
        for t in submission_tasks
    )
    candidates["Submit_pct"] = {
        "candidate_formula": "count of nonmissing timestamps / 6 * 100",
        "max_abs_diff": float((submitted - fe["Submit_pct"]).abs().max()),
    }
    candidates["Ketepatan_pct"] = {
        "candidate_formula": "count of timestamp <= corresponding deadline / 6 * 100",
        "max_abs_diff": float((on_time_count / 6 * 100 - fe["Ketepatan_pct"]).abs().max()),
        "mismatch_rows_at_1e_minus_8": int(((on_time_count / 6 * 100 - fe["Ketepatan_pct"]).abs() > 1e-8).sum()),
        "submitted_timestamps_after_deadline": int(sum(
            (raw[f"Timestamp_{t}"] > raw[f"Deadline_{t}"]).sum()
            for t in submission_tasks
        )),
    }
    date_on_time_count = sum(
        (raw[f"Timestamp_{t}"].dt.normalize() <= raw[f"Deadline_{t}"].dt.normalize()).astype(int)
        for t in submission_tasks
    )
    candidates["Ketepatan_pct"]["calendar_date_comparison_mismatch_rows"] = int(
        ((date_on_time_count / 6 * 100 - fe["Ketepatan_pct"]).abs() > 1e-8).sum()
    )
    manifest["raw_fe_candidate_checks"] = candidates
    manifest["raw_timestamp_quality"] = {
        c: {"dtype": str(raw[c].dtype), "missing": int(raw[c].isna().sum()),
            "text_sentinel_counts": {
                marker: int(raw[c].astype(str).str.strip().eq(marker).sum())
                for marker in ("-", "0", "NaT", "Tidak Submit", "Belum Submit")
            }}
        for c in raw.columns if c.startswith(("Timestamp_", "Deadline_"))
    }
    after = hashes()
    manifest["original_sha256_before"] = before
    manifest["original_sha256_after"] = after
    manifest["all_originals_unchanged"] = before == after
    if before != after:
        raise RuntimeError("Original artifacts changed during audit")
    output = ROOT / "audit/artifact_manifest.json"
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, default=native), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in (
        "executable", "alignment", "feature_quality", "load_warnings", "model", "scaler",
        "predictions", "raw_fe_candidate_checks", "raw_timestamp_quality", "all_originals_unchanged",
    )}, indent=2, ensure_ascii=False, default=native))
    print("Saved:", output)


if __name__ == "__main__":
    main()
