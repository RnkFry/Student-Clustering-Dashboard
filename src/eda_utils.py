"""Basic dataset metadata; full EDA is deferred to the next stage."""

import pandas as pd
import streamlit as st

from src import config


def dataset_overview(df: pd.DataFrame) -> dict[str, int]:
    return {
        "records": len(df),
        "columns": len(df.columns),
        "unique_nim": int(df["NIM"].nunique()) if "NIM" in df else 0,
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }


def numerical_columns(df: pd.DataFrame) -> list[str]:
    excluded = set(config.IDENTIFIER_COLUMNS + (config.CLUSTER_COLUMN,))
    return [column for column in df.select_dtypes(include="number") if column not in excluded]


@st.cache_data(show_spinner=False)
def missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    counts = df.isna().sum()
    return pd.DataFrame({"Kolom": counts.index, "Missing": counts.values,
                         "Missing (%)": counts.values / max(len(df), 1) * 100}).sort_values("Missing", ascending=False)


@st.cache_data(show_spinner=False)
def descriptive_statistics(df: pd.DataFrame) -> pd.DataFrame:
    columns = numerical_columns(df)
    return df[columns].describe().T if columns and not df.empty else pd.DataFrame()


@st.cache_data(show_spinner=False)
def outlier_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in numerical_columns(df):
        values = df[column].dropna()
        q1, q3 = values.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        count = int(((values < lower) | (values > upper)).sum())
        rows.append({"Fitur": column, "Q1": q1, "Q3": q3, "IQR": iqr,
                     "Batas bawah": lower, "Batas atas": upper, "Record ekstrem": count})
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def correlation_matrix(df: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
    return df[list(columns)].corr()


def summarize_clusters(df: pd.DataFrame) -> pd.DataFrame:
    """Include absent clusters with zero counts and undefined means."""
    group = df.groupby(config.CLUSTER_COLUMN)
    summary = group.size().reindex(range(4), fill_value=0).rename("Record_Count").to_frame()
    summary.index.name = config.CLUSTER_COLUMN
    summary["Record_Percentage"] = summary["Record_Count"] / max(len(df), 1) * 100
    summary["Unique_NIM_Count"] = group["NIM"].nunique().reindex(range(4), fill_value=0)
    means = group[list(config.MODEL_FEATURES + config.LO_FEATURES)].mean().add_prefix("Mean_")
    return summary.join(means).reset_index()


def _column_description(column: str) -> tuple[str, str]:
    if column in config.IDENTIFIER_COLUMNS:
        return "Identifier", "Penanda record; tidak digunakan sebagai input clustering."
    if column in config.LO_FEATURES:
        description = "Jumlah avg_LO1, avg_LO2, dan avg_LO3." if column == "Total_LO" else "Rata-rata komponen LO dari sembilan assessment, cocok secara numerik pada audit."
        return "Analisis eksternal", description
    if column in config.MODEL_FEATURES:
        if column in ("Course_pct", "Dosen_pct", "Ketepatan_pct"):
            description = "Fitur persentase model. Rumus/provenance asli masih perlu konfirmasi."
        elif column == "Submit_pct":
            description = "Cocok numerik dengan jumlah enam timestamp terisi / 6 × 100 pada audit."
        else:
            description = "Cocok numerik dengan rata-rata sepuluh indikator biner terkait × 100 pada audit."
        return "Input model", description
    if column == config.CLUSTER_COLUMN:
        return "Hasil reporting", "Label K-Means tersimpan 0–3; bukan urutan kualitas mahasiswa."
    if column.startswith("Timestamp_"):
        return "Waktu pengumpulan", "Timestamp tugas; missing terkait tugas tanpa timestamp pengumpulan."
    if column.startswith("Deadline_"):
        return "Deadline", "Batas waktu tugas sebagaimana tersimpan dalam raw data."
    if column.startswith("TLE_"):
        return "TLE", "Butir TLE; makna dan skala rinci perlu dikonfirmasi dari data dictionary sumber."
    if column.startswith(("FD", "LN", "PPT", "VBL")):
        return "Aktivitas", "Indikator aktivitas 0/1 pada sesi terkait sebagaimana raw data."
    return "Assessment", "Komponen LO atau total nilai assessment sebagaimana raw data."


def data_dictionary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in df:
        role, description = _column_description(column)
        rows.append({"Kolom": column, "Tipe": str(df[column].dtype), "Kelompok": role,
                     "Input model": column in config.MODEL_FEATURES, "Keterangan": description})
    return pd.DataFrame(rows)
