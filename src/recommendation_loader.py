"""Read the Prodi workbook without copying or rewriting its recommendation text."""

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import re

import pandas as pd
import streamlit as st

from src import config

RECOMMENDATION_PATH = config.DATA_DIR / "reference" / "Rekomendasi Prodi.xlsx"
RECOMMENDATION_SHEET = "Sheet1"
RECOMMENDATION_COLUMNS = (
    "Cluster dan nama profil",
    "Karakteristik empiris",
    "Rekomendasi strategis untuk pengelola Prodi pada semester berikutnya",
)
# Identity contract from FEATURE_REKOMENDASI_PRODI.md, not recommendation content.
EXPECTED_PROFILES = {
    0: "High Achievement and Consistent Engagement",
    1: "Critical Engagement and Assessment Support",
    2: "Developing Learning Engagement and LO Attainment",
    3: "Learning Engagement and Achievement Improvement",
}


class RecommendationError(ValueError):
    """Recommendation input cannot be used without guessing its meaning."""


@dataclass(frozen=True)
class Recommendation:
    cluster_id: int
    profile_name: str
    empirical_characteristics: str
    strategic_recommendations: str
    excel_row: int


def _is_blank(value: object) -> bool:
    return bool(pd.isna(value)) or (isinstance(value, str) and not value.strip())


def normalize_recommendations(
    frame: pd.DataFrame, *, first_data_row: int = 10,
) -> dict[int, Recommendation]:
    """Validate a table with the actual Excel headers, independent of row order."""
    columns = [column.strip() if isinstance(column, str) else column for column in frame.columns]
    if pd.Index(columns).has_duplicates:
        raise RecommendationError("Nama kolom rekomendasi duplikat.")
    if set(columns) != set(RECOMMENDATION_COLUMNS):
        raise RecommendationError(
            "Schema rekomendasi tidak cocok. Kolom wajib: " + "; ".join(RECOMMENDATION_COLUMNS)
        )
    table = frame.copy()
    table.columns = columns
    mapping: dict[int, Recommendation] = {}
    for position, values in enumerate(table.loc[:, list(RECOMMENDATION_COLUMNS)].itertuples(index=False, name=None)):
        row_number = first_data_row + position
        if all(_is_blank(value) for value in values):
            continue
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise RecommendationError(f"Baris Excel {row_number}: profil, karakteristik, dan rekomendasi wajib berupa teks tidak kosong.")
        profile, empirical, strategy = values
        match = re.fullmatch(r"Cluster\s+(\d+)\s*[—–-]\s*(.+)", profile.strip())
        if match is None:
            raise RecommendationError(f"Baris Excel {row_number}: format harus 'Cluster <ID> — <nama profil>'.")
        cluster_id = int(match.group(1))
        if cluster_id not in EXPECTED_PROFILES:
            raise RecommendationError(f"Cluster {cluster_id} tidak dikenal; ID wajib 0–3.")
        if cluster_id in mapping:
            raise RecommendationError(f"Mapping Cluster {cluster_id} duplikat pada baris Excel {row_number}.")
        name = match.group(2).strip()
        if name != EXPECTED_PROFILES[cluster_id]:
            raise RecommendationError(f"Nama profil Cluster {cluster_id} tidak sesuai kontrak final. Periksa ID/nama di Excel; label tidak diubah otomatis.")
        mapping[cluster_id] = Recommendation(cluster_id, name, empirical, strategy, row_number)
    missing = sorted(set(EXPECTED_PROFILES) - mapping.keys())
    if missing:
        raise RecommendationError(f"Mapping cluster tidak lengkap; missing ID: {missing}.")
    return dict(sorted(mapping.items()))


@st.cache_data(show_spinner=False)
def _read_recommendation_workbook(content: bytes) -> dict[int, Recommendation]:
    """Cache by workbook content so edits at the same path invalidate the result."""
    try:
        with pd.ExcelFile(BytesIO(content), engine="openpyxl") as workbook:
            if RECOMMENDATION_SHEET not in workbook.sheet_names:
                raise RecommendationError(f"Sheet '{RECOMMENDATION_SHEET}' tidak tersedia. Sheet ditemukan: {workbook.sheet_names}.")
            raw = pd.read_excel(workbook, sheet_name=RECOMMENDATION_SHEET, header=None, dtype=object, keep_default_na=False)
    except RecommendationError:
        raise
    except Exception as exc:
        raise RecommendationError(f"Workbook rekomendasi tidak dapat dibaca: {exc}") from exc

    # The supplied workbook has a title/padding and its actual header at B9:D9.
    # Locate by labels, never interpret the title or blank columns as mappings.
    header_rows = [
        position for position, values in enumerate(raw.itertuples(index=False, name=None))
        if RECOMMENDATION_COLUMNS[0] in [value.strip() if isinstance(value, str) else value for value in values]
    ]
    if len(header_rows) != 1:
        raise RecommendationError("Schema rekomendasi: diperlukan tepat satu baris header 'Cluster dan nama profil'.")
    header_row = header_rows[0]
    table = raw.iloc[header_row:].copy()
    table = table.loc[:, [not all(_is_blank(value) for value in table[column]) for column in table.columns]]
    table.columns = table.iloc[0].tolist()
    return normalize_recommendations(table.iloc[1:], first_data_row=header_row + 2)


def load_recommendations(path: Path | None = None) -> dict[int, Recommendation]:
    """Load Sheet1 using pandas/openpyxl; never modify the source workbook."""
    source = Path(path) if path is not None else RECOMMENDATION_PATH
    try:
        content = source.read_bytes()
    except OSError as exc:
        raise RecommendationError(
            "File rekomendasi tidak tersedia atau tidak dapat dibaca. "
            "Periksa data/reference/Rekomendasi Prodi.xlsx dan izin bacanya."
        ) from exc
    return _read_recommendation_workbook(content)
