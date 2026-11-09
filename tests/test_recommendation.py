"""Workbook fidelity, strict identity mapping, external LO, and Streamlit integration."""

from contextlib import ExitStack
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import RobustScaler
from streamlit.testing.v1 import AppTest

from src import config
from src.data_loader import load_reporting_data, sha256_file, verify_originals
from src.recommendation_loader import (
    EXPECTED_PROFILES, RECOMMENDATION_COLUMNS, RECOMMENDATION_PATH,
    RecommendationError, load_recommendations, normalize_recommendations,
)
from src.recommendation_service import get_cluster_recommendation
from src.ui_utils import apply_reporting_filters


class RecommendationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = pd.read_excel(RECOMMENDATION_PATH, sheet_name="Sheet1", header=8,
                                   usecols="B:D", engine="openpyxl", keep_default_na=False)
        cls.mapping = load_recommendations()
        cls.full = load_reporting_data()
        cls.originals = verify_originals()
        cls.hashes = {path: sha256_file(path) for path in (
            RECOMMENDATION_PATH, config.CLUSTERED_DATA_PATH,
            config.CLUSTER_SUMMARY_PATH, config.REPORTING_MANIFEST_PATH,
        )}

    @classmethod
    def tearDownClass(cls) -> None:
        if verify_originals() != cls.originals or any(sha256_file(path) != digest for path, digest in cls.hashes.items()):
            raise AssertionError("Recommendation feature modified source/reporting artifacts")

    def test_actual_workbook_mapping_and_exact_text_for_all_clusters(self) -> None:
        self.assertEqual(list(self.mapping), [0, 1, 2, 3])
        for cluster in range(4):
            with self.subTest(cluster=cluster):
                entry = self.mapping[cluster]
                source = self.source.iloc[cluster]
                self.assertEqual(entry.cluster_id, cluster)
                self.assertEqual(entry.profile_name, EXPECTED_PROFILES[cluster])
                self.assertEqual(source.iloc[0], f"Cluster {cluster} — {entry.profile_name}")
                self.assertEqual(entry.empirical_characteristics, source.iloc[1])
                self.assertEqual(entry.strategic_recommendations, source.iloc[2])
                self.assertEqual(entry.excel_row, cluster + 10)

    def test_row_order_does_not_relabel_clusters(self) -> None:
        reordered = normalize_recommendations(self.source.iloc[::-1])
        for cluster in range(4):
            self.assertEqual(reordered[cluster].strategic_recommendations, self.mapping[cluster].strategic_recommendations)

    def test_duplicate_missing_unknown_and_swapped_identity(self) -> None:
        cases = [
            (pd.concat([self.source, self.source.iloc[:1]]), "duplikat"),
            (self.source.iloc[:3], "missing ID: \\[3\\]"),
            (self.source.iloc[:0], "missing ID"),
        ]
        unknown = self.source.copy()
        unknown.iloc[0, 0] = unknown.iloc[0, 0].replace("Cluster 0", "Cluster 4")
        cases.append((unknown, "tidak dikenal"))
        swapped = self.source.copy()
        swapped.iloc[0, 0] = swapped.iloc[0, 0].replace("Cluster 0", "Cluster 1")
        cases.append((swapped, "tidak sesuai kontrak"))
        for frame, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(RecommendationError, message):
                    normalize_recommendations(frame)

    def test_schema_blank_content_and_invalid_cluster_format(self) -> None:
        with self.assertRaisesRegex(RecommendationError, "Schema"):
            normalize_recommendations(self.source.drop(columns=RECOMMENDATION_COLUMNS[2]))
        duplicate = pd.concat([self.source, self.source.iloc[:, :1]], axis=1)
        with self.assertRaisesRegex(RecommendationError, "kolom.*duplikat"):
            normalize_recommendations(duplicate)
        for column in range(3):
            bad = self.source.copy()
            bad.iloc[0, column] = " "
            with self.assertRaisesRegex(RecommendationError, "teks tidak kosong"):
                normalize_recommendations(bad)
        for label in ("Cluster -1 — Invalid", "Cluster 0.5 — Invalid", "0", True):
            bad = self.source.astype(object).copy()
            bad.iloc[0, 0] = label
            with self.assertRaises(RecommendationError):
                normalize_recommendations(bad)

    def test_loader_detects_missing_file_sheet_corruption_and_duplicate_header(self) -> None:
        with tempfile.TemporaryDirectory(prefix="recommendation-test-") as directory:
            candidate = Path(directory) / "reference.xlsx"
            with self.assertRaisesRegex(RecommendationError, "File rekomendasi"):
                load_recommendations(candidate)
            candidate.write_bytes(b"not an xlsx")
            with self.assertRaisesRegex(RecommendationError, "tidak dapat dibaca"):
                load_recommendations(candidate)
            self.source.to_excel(candidate, sheet_name="WrongSheet", index=False, engine="openpyxl")
            with self.assertRaisesRegex(RecommendationError, "Sheet1"):
                load_recommendations(candidate)
            duplicate = pd.concat([self.source, self.source.iloc[:, :1]], axis=1)
            duplicate.to_excel(candidate, index=False, engine="openpyxl")
            with self.assertRaisesRegex(RecommendationError, "kolom.*duplikat"):
                load_recommendations(candidate)

    def test_loader_cache_changes_with_file_content_and_keeps_newlines(self) -> None:
        with tempfile.TemporaryDirectory(prefix="recommendation-cache-test-") as directory:
            candidate = Path(directory) / "reference.xlsx"
            self.source.to_excel(candidate, index=False, startrow=8, startcol=1, engine="openpyxl")
            first = load_recommendations(candidate)
            changed = self.source.copy()
            # Modify only a disposable copy, using another existing Excel text.
            changed.iloc[0, 2] = self.source.iloc[1, 2]
            changed.to_excel(candidate, index=False, startrow=8, startcol=1, engine="openpyxl")
            second = load_recommendations(candidate)
            self.assertNotEqual(first[0].strategic_recommendations, second[0].strategic_recommendations)
            self.assertEqual(second[0].strategic_recommendations, changed.iloc[0, 2])

    def test_service_uses_actual_filtered_means_without_model_calls(self) -> None:
        before = self.full.copy(deep=True)
        period = self.full.iloc[0]["Kode_Periode"]
        visible = apply_reporting_filters(self.full, periods=[period])
        with ExitStack() as stack:
            for cls, method in ((KMeans, "fit"), (KMeans, "fit_predict"), (KMeans, "predict"),
                                (RobustScaler, "fit"), (RobustScaler, "fit_transform"), (RobustScaler, "transform")):
                stack.enter_context(patch.object(cls, method, side_effect=AssertionError("No ML operation allowed")))
            for cluster in range(4):
                result = get_cluster_recommendation(cluster, self.mapping, visible)
                subset = visible.loc[visible.Cluster == cluster]
                self.assertEqual(result.record_count, len(subset))
                self.assertEqual(result.unique_student_count, subset.NIM.nunique())
                self.assertEqual(result.feature_profile.Fitur.tolist(), list(config.MODEL_FEATURES))
                self.assertEqual(result.lo_profile.Fitur.tolist(), list(config.LO_FEATURES))
                for profile in (result.feature_profile, result.lo_profile):
                    np.testing.assert_allclose(profile["Rata-rata"].astype(float), subset[profile.Fitur].mean(), equal_nan=True)
        pd.testing.assert_frame_equal(self.full, before)

    def test_lo_changes_do_not_change_mapping_features_or_labels(self) -> None:
        changed = self.full.copy()
        changed.loc[:, list(config.LO_FEATURES)] *= 0.5
        for cluster in range(4):
            original = get_cluster_recommendation(cluster, self.mapping, self.full)
            modified = get_cluster_recommendation(cluster, self.mapping, changed)
            self.assertEqual(original.recommendation, modified.recommendation)
            pd.testing.assert_frame_equal(original.feature_profile, modified.feature_profile)
            np.testing.assert_allclose(modified.lo_profile["Rata-rata"], original.lo_profile["Rata-rata"] * 0.5)
        pd.testing.assert_series_equal(changed.Cluster, self.full.Cluster)

    def test_service_unknown_missing_mapping_and_invalid_reporting_labels(self) -> None:
        for cluster in (-1, 4, True, "0", 0.5, None):
            with self.subTest(cluster=cluster), self.assertRaisesRegex(RecommendationError, "tidak dikenal"):
                get_cluster_recommendation(cluster, self.mapping, self.full)
        with self.assertRaisesRegex(RecommendationError, "Mapping Cluster 0 tidak tersedia"):
            get_cluster_recommendation(0, {}, self.full)
        with self.assertRaisesRegex(RecommendationError, "Label Cluster tidak tersedia"):
            get_cluster_recommendation(0, self.mapping, self.full.drop(columns="Cluster"))
        for label in (4, True, 0.5, None):
            bad = self.full.assign(Cluster=label)
            with self.assertRaisesRegex(RecommendationError, "Label reporting"):
                get_cluster_recommendation(0, self.mapping, bad)

    def test_missing_and_invalid_profiles_do_not_create_replacement_numbers(self) -> None:
        missing = self.full.drop(columns=["FD_pct", "avg_LO1", "NIM"])
        result = get_cluster_recommendation(0, self.mapping, missing)
        self.assertIsNone(result.unique_student_count)
        for profile, feature in ((result.feature_profile, "FD_pct"), (result.lo_profile, "avg_LO1")):
            row = profile.set_index("Fitur").loc[feature]
            self.assertTrue(pd.isna(row["Rata-rata"]))
            self.assertEqual(row["Status"], "Kolom tidak tersedia")
        for value in (np.nan, np.inf, True, "invalid"):
            invalid = self.full.assign(avg_LO1=value)
            profile = get_cluster_recommendation(0, self.mapping, invalid).lo_profile
            self.assertTrue(pd.isna(profile.set_index("Fitur").loc["avg_LO1", "Rata-rata"]))
        empty = get_cluster_recommendation(1, self.mapping, self.full.loc[self.full.Cluster == 0])
        self.assertEqual(empty.record_count, 0)
        self.assertTrue(empty.feature_profile["Rata-rata"].isna().all())

    def app(self) -> AppTest:
        app = AppTest.from_file(str(config.PROJECT_ROOT / "app.py"), default_timeout=30).run()
        return app.sidebar.radio[0].set_value("Rekomendasi Strategis Prodi").run()

    def test_ui_all_clusters_source_text_profiles_and_filter(self) -> None:
        app = self.app()
        for cluster in range(4):
            app.selectbox(key="recommendation_cluster").set_value(cluster).run()
            self.assertFalse(app.exception)
            self.assertFalse(app.error)
            texts = [item.value for item in app.text]
            # Streamlit's st.text strips outer whitespace; internal text/newlines stay intact.
            self.assertIn(self.mapping[cluster].strategic_recommendations.strip(), texts)
            self.assertIn(self.mapping[cluster].empirical_characteristics, texts)
            self.assertEqual(len(app.dataframe), 2)
            self.assertEqual(len(app.get("vega_lite_chart")), 2)
        app.multiselect(key="filter_clusters").set_value([0]).run()
        self.assertTrue(any("tidak memiliki record" in item.value for item in app.info))
        self.assertFalse(app.dataframe)
        app.multiselect(key="filter_clusters").set_value([]).run()
        self.assertFalse(app.exception)
        self.assertTrue(app.info)

    def test_ui_invalid_workbook_error_does_not_break_other_sections(self) -> None:
        with patch("sections.recommendation.load_recommendations", side_effect=RecommendationError("Mapping Cluster 0 duplikat")):
            app = self.app()
            self.assertFalse(app.exception)
            self.assertTrue(any("duplikat" in item.value for item in app.error))
            self.assertFalse(app.text)
            app.sidebar.radio[0].set_value("Home / Executive Summary").run()
            self.assertFalse(app.error)

    def test_ui_unavailable_lo_and_feature_show_explicit_status(self) -> None:
        missing = self.full.drop(columns=["FD_pct", "avg_LO1"])
        with patch("sections.recommendation.reporting_view", return_value=(missing, missing)):
            app = self.app()
            self.assertFalse(app.exception)
            self.assertFalse(app.error)
            self.assertTrue(any("FD_pct" in item.value for item in app.warning))
            self.assertTrue(any("avg_LO1" in item.value for item in app.warning))


if __name__ == "__main__":
    unittest.main()
