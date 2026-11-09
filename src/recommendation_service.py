"""Rule-based lookup plus descriptive evidence from existing reporting labels."""

from collections.abc import Mapping
from dataclasses import dataclass
from numbers import Integral

import numpy as np
import pandas as pd

from src import config
from src.recommendation_loader import EXPECTED_PROFILES, Recommendation, RecommendationError


@dataclass(frozen=True)
class ClusterRecommendation:
    recommendation: Recommendation
    record_count: int
    unique_student_count: int | None
    feature_profile: pd.DataFrame
    lo_profile: pd.DataFrame


def _summarize_profile(records: pd.DataFrame, features: tuple[str, ...]) -> pd.DataFrame:
    rows = []
    for feature in features:
        mean = None
        count = 0
        if feature not in records:
            status = "Kolom tidak tersedia"
        elif records.empty:
            status = "Tidak ada record pada filter aktif"
        else:
            values = records[feature]
            if not pd.api.types.is_numeric_dtype(values) or pd.api.types.is_bool_dtype(values):
                status = "Data harus numerik"
            else:
                valid = np.isfinite(values.to_numpy(dtype=float, na_value=np.nan))
                count = int(valid.sum())
                if count == len(records):
                    mean = float(values.mean())
                    status = "Tersedia"
                else:
                    status = "Data mengandung nilai kosong/tidak finite; rata-rata tidak dihitung"
        rows.append({"Fitur": feature, "Rata-rata": mean, "Record valid": count, "Status": status})
    return pd.DataFrame(rows)


def get_cluster_recommendation(
    cluster_id: int, mapping: Mapping[int, Recommendation], reporting: pd.DataFrame,
) -> ClusterRecommendation:
    """Select by saved cluster ID. LO never influences the selection or labels."""
    if isinstance(cluster_id, bool) or not isinstance(cluster_id, Integral) or cluster_id not in EXPECTED_PROFILES:
        raise RecommendationError(f"Cluster {cluster_id!r} tidak dikenal; pilih integer 0–3.")
    if cluster_id not in mapping:
        raise RecommendationError(f"Mapping Cluster {cluster_id} tidak tersedia. Periksa workbook rekomendasi.")
    recommendation = mapping[cluster_id]
    if recommendation.cluster_id != cluster_id or recommendation.profile_name != EXPECTED_PROFILES[cluster_id]:
        raise RecommendationError(f"Mapping Cluster {cluster_id} tidak cocok dengan identitas profil final.")
    if reporting.columns.has_duplicates:
        raise RecommendationError("Kolom reporting duplikat; profil tidak dapat dihitung.")
    if config.CLUSTER_COLUMN not in reporting:
        raise RecommendationError("Label Cluster tidak tersedia. Dibutuhkan data/processed/clustered_data.csv dengan label final tersimpan.")
    labels = reporting[config.CLUSTER_COLUMN]
    if not reporting.empty and (
        not pd.api.types.is_integer_dtype(labels) or pd.api.types.is_bool_dtype(labels)
        or labels.isna().any() or not labels.isin(EXPECTED_PROFILES).all()
    ):
        raise RecommendationError("Label reporting harus integer Cluster 0–3; label tidak dikoreksi otomatis.")
    subset = reporting.loc[labels == cluster_id]
    unique_count = int(subset["NIM"].nunique()) if "NIM" in subset and not subset["NIM"].isna().any() else None
    return ClusterRecommendation(
        recommendation=recommendation,
        record_count=len(subset),
        unique_student_count=unique_count,
        feature_profile=_summarize_profile(subset, config.MODEL_FEATURES),
        lo_profile=_summarize_profile(subset, config.LO_FEATURES),
    )
