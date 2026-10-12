"""Simple Vega-Lite charts and a cached, fixed PCA projection for reporting."""

import numpy as np
import pandas as pd
import streamlit as st

from src import config
from src.clustering_utils import load_model_and_scaler, prepare_model_input
from src.eda_utils import correlation_matrix
from src.ui_utils import cluster_label

CLUSTER_COLORS = ["#4477AA", "#EE6677", "#228833", "#CCBB44"]
CLUSTER_COLOR_SCALE = {"domain": [cluster_label(i) for i in range(4)], "range": CLUSTER_COLORS}


def histogram(df: pd.DataFrame, feature: str) -> None:
    values = df[[feature]].rename(columns={feature: "Value"}).dropna()
    st.vega_lite_chart(values, {
        "mark": {"type": "bar", "color": "#4477AA"},
        "encoding": {
            "x": {"field": "Value", "type": "quantitative", "bin": {"maxbins": 30}, "title": feature},
            "y": {"aggregate": "count", "type": "quantitative", "title": "Jumlah record"},
            "tooltip": [{"aggregate": "count", "type": "quantitative", "title": "Record"}],
        }, "height": 280,
    }, width="stretch")


def boxplot(df: pd.DataFrame, feature: str, *, by_cluster: bool = False) -> None:
    data = pd.DataFrame({"Value": df[feature]})
    encoding = {"y": {"field": "Value", "type": "quantitative", "title": feature}}
    if by_cluster:
        data["Cluster"] = df[config.CLUSTER_COLUMN].map(cluster_label)
        encoding["x"] = {"field": "Cluster", "type": "nominal", "sort": CLUSTER_COLOR_SCALE["domain"]}
        encoding["color"] = {"field": "Cluster", "type": "nominal", "scale": CLUSTER_COLOR_SCALE, "legend": None}
    st.vega_lite_chart(data, {"mark": {"type": "boxplot", "extent": 1.5}, "encoding": encoding, "height": 280}, width="stretch")


def heatmap(matrix: pd.DataFrame, *, domain=None, title: str = "Nilai") -> None:
    rows = [{"Row": str(row), "Feature": str(column), "Value": float(value)}
            for row in matrix.index for column, value in matrix.loc[row].items() if pd.notna(value)]
    if not rows:
        st.info("Heatmap tidak tersedia untuk fitur konstan atau pilihan data ini.")
        return
    scale = {"scheme": "redblue", "domain": [-1, 1]} if domain == [-1, 1] else {"scheme": "blues"}
    if domain is not None:
        scale["domain"] = domain
    st.vega_lite_chart(pd.DataFrame(rows), {
        "mark": "rect", "encoding": {
            "x": {"field": "Feature", "type": "ordinal", "sort": list(matrix.columns), "title": None},
            "y": {"field": "Row", "type": "ordinal", "sort": [str(i) for i in matrix.index], "title": None},
            "color": {"field": "Value", "type": "quantitative", "scale": scale, "title": title},
            "tooltip": [{"field": "Row"}, {"field": "Feature"}, {"field": "Value", "format": ".3f"}],
        }, "height": max(180, min(len(matrix) * 32, 500)),
    }, width="stretch")


def render_correlation(df: pd.DataFrame, features: list[str], *, key: str) -> None:
    selected = st.multiselect("Fitur korelasi", features, default=features[:8], max_selections=16, key=key)
    if len(selected) < 2:
        st.info("Pilih sedikitnya dua fitur numerik untuk korelasi.")
        return
    matrix = correlation_matrix(df, tuple(selected))
    heatmap(matrix, domain=[-1, 1], title="Pearson r")
    st.dataframe(matrix.round(3), width="stretch")
    st.caption("Korelasi menunjukkan asosiasi, bukan sebab-akibat. Nilai NaN dapat berasal dari fitur konstan.")


def cluster_size_chart(summary: pd.DataFrame) -> None:
    data = summary[["Cluster", "Record_Count"]].copy()
    data["Cluster"] = data["Cluster"].map(cluster_label)
    st.vega_lite_chart(data, {
        "mark": "bar", "encoding": {
            "x": {"field": "Cluster", "type": "nominal", "sort": CLUSTER_COLOR_SCALE["domain"]},
            "y": {"field": "Record_Count", "type": "quantitative", "title": "Jumlah record"},
            "color": {"field": "Cluster", "type": "nominal", "scale": CLUSTER_COLOR_SCALE, "legend": None},
            "tooltip": [{"field": "Cluster"}, {"field": "Record_Count", "title": "Record"}],
        }, "height": 260,
    }, width="stretch")


def radar_chart(means: pd.DataFrame) -> None:
    features = list(config.MODEL_FEATURES)
    angles = np.linspace(0, 2 * np.pi, len(features), endpoint=False)
    axes = [{"X0": 0, "Y0": 0, "X": float(100*np.sin(a)), "Y": float(100*np.cos(a)),
             "LabelX": float(120*np.sin(a)), "LabelY": float(120*np.cos(a)), "Feature": f}
            for a, f in zip(angles, features)]
    rings, points = [], []
    for radius in (20, 40, 60, 80, 100):
        for order in range(len(features) + 1):
            angle = angles[order % len(features)]
            rings.append({"X": float(radius*np.sin(angle)), "Y": float(radius*np.cos(angle)), "Ring": radius, "Order": order})
    for cluster, row in means.iterrows():
        if row[features].isna().any():
            continue
        for order in range(len(features) + 1):
            i = order % len(features)
            radius = float(row[features[i]])
            points.append({"X": radius*float(np.sin(angles[i])), "Y": radius*float(np.cos(angles[i])),
                           "Cluster": cluster_label(cluster), "Order": order})
    position = {
        "x": {"field": "X", "type": "quantitative", "axis": None, "scale": {"domain": [-145, 145]}},
        "y": {"field": "Y", "type": "quantitative", "axis": None, "scale": {"domain": [-145, 145]}},
    }
    st.vega_lite_chart(spec={
        "height": 400,
        "layer": [
            {"data": {"values": rings}, "mark": {"type": "line", "color": "#dddddd"},
             "encoding": {**position, "detail": {"field": "Ring"}, "order": {"field": "Order", "type": "quantitative"}}},
            {"data": {"values": axes}, "mark": {"type": "rule", "color": "#dddddd"},
             "encoding": {**position, "x2": {"field": "X0"}, "y2": {"field": "Y0"}}},
            {"data": {"values": axes}, "mark": {"type": "text", "fontSize": 10},
             "encoding": {"x": {**position["x"], "field": "LabelX"}, "y": {**position["y"], "field": "LabelY"}, "text": {"field": "Feature"}}},
            {"data": {"values": points}, "mark": {"type": "line", "strokeWidth": 2},
             "encoding": {**position, "color": {"field": "Cluster", "type": "nominal", "scale": CLUSTER_COLOR_SCALE},
                          "order": {"field": "Order", "type": "quantitative"}}},
        ],
    }, width="stretch")
    st.caption("Radar memakai rata-rata delapan fitur pada skala persentase asli 0–100; garis skala berjarak 20 poin.")


@st.cache_data(show_spinner=False)
def pca_projection(full_reporting: pd.DataFrame) -> tuple[pd.DataFrame, tuple[float, float]]:
    """SVD PCA on the entire reporting matrix. No clustering/scaler fit operation."""
    scaler, _ = load_model_and_scaler()
    values = scaler.transform(prepare_model_input(full_reporting))
    if not np.isfinite(values).all():
        raise config.ModelContractError("Matriks proyeksi PCA mengandung nilai nonfinite.")
    centered = values - values.mean(axis=0)
    u, singular, _ = np.linalg.svd(centered, full_matrices=False)
    coordinates = u[:, :2] * singular[:2]
    denominator = float((singular**2).sum())
    ratio = singular[:2]**2 / denominator if denominator else np.zeros(2)
    return pd.DataFrame(coordinates, index=full_reporting.index, columns=["PC1", "PC2"]), (float(ratio[0]), float(ratio[1]))


def pca_chart(full: pd.DataFrame, visible: pd.DataFrame) -> None:
    coordinates, variance = pca_projection(full)
    data = coordinates.loc[visible.index].copy()
    data["Cluster"] = visible[config.CLUSTER_COLUMN].map(cluster_label)
    limit = st.selectbox("Batas titik PCA", [500, 1000, 2000, 6000], index=2, key="pca_point_limit")
    if len(data) > limit:
        data = data.sample(n=limit, random_state=42)
        st.caption(f"Menampilkan sampel tetap {limit:,} dari {len(visible):,} record pada filter aktif.")
    st.vega_lite_chart(data, {
        "mark": {"type": "point", "filled": True, "opacity": 0.45, "size": 25},
        "encoding": {
            "x": {"field": "PC1", "type": "quantitative", "title": f"PC1 ({variance[0]:.2%})"},
            "y": {"field": "PC2", "type": "quantitative", "title": f"PC2 ({variance[1]:.2%})"},
            "color": {"field": "Cluster", "type": "nominal", "scale": CLUSTER_COLOR_SCALE},
            "tooltip": [{"field": "Cluster"}, {"field": "PC1", "format": ".3f"}, {"field": "PC2", "format": ".3f"}],
        }, "height": 360,
    }, width="stretch")
    st.caption("PCA adalah proyeksi untuk visualisasi. Koordinat dihitung sekali dari seluruh reporting dengan scaler tersimpan; filter hanya memilih titik. Label cluster tetap.")
