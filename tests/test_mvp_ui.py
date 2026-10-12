"""MVP regressions: filters preserve labels, no fitting, exports and empty states."""

from contextlib import ExitStack
from io import BytesIO
import json
import unittest
from unittest.mock import patch

import altair as alt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import RobustScaler
from streamlit.testing.v1 import AppTest

from sections.download_result import export_payloads
from src import config
from src.data_loader import load_reporting_data, sha256_file, verify_originals
from src.eda_utils import summarize_clusters
from src.ui_utils import apply_reporting_filters
from src.visualization import pca_projection


class MvpUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.full = load_reporting_data()
        cls.originals = verify_originals()
        cls.reporting_hashes = {
            path: sha256_file(path) for path in
            (config.CLUSTERED_DATA_PATH, config.CLUSTER_SUMMARY_PATH, config.REPORTING_MANIFEST_PATH)
        }

    @classmethod
    def tearDownClass(cls):
        if verify_originals() != cls.originals:
            raise AssertionError("Original sources changed")
        if {p: sha256_file(p) for p in cls.reporting_hashes} != cls.reporting_hashes:
            raise AssertionError("UI wrote to reporting artifacts")

    def app(self):
        return AppTest.from_file(str(config.PROJECT_ROOT / "app.py"), default_timeout=30).run()

    def assert_no_errors(self, app):
        self.assertFalse(app.exception, [e.message for e in app.exception])
        self.assertFalse(app.error, [e.value for e in app.error])

    def test_all_menus_and_chart_schemas_without_fit_or_prediction(self):
        with ExitStack() as stack:
            for cls, name in (
                (KMeans, "fit"), (KMeans, "fit_predict"), (KMeans, "predict"),
                (RobustScaler, "fit"), (RobustScaler, "fit_transform"),
            ):
                stack.enter_context(patch.object(cls, name, side_effect=AssertionError("UI must use saved labels")))
            app = self.app()
            self.assertEqual(len(app.sidebar.radio[0].options), 8)
            chart_count = 0
            for menu in app.sidebar.radio[0].options:
                with self.subTest(menu=menu):
                    app.sidebar.radio[0].set_value(menu).run()
                    self.assert_no_errors(app)
                    for chart in app.get("vega_lite_chart"):
                        spec = json.loads(chart.proto.spec)
                        # Streamlit sends data separately; frontend adds this named dataset.
                        if "data" not in spec and "layer" not in spec:
                            spec["data"] = {"name": "app_data"}
                        alt.vegalite.v6.schema.TopLevelSpec.from_dict(spec, validate=True)
                        chart_count += 1
            self.assertGreaterEqual(chart_count, 10)
            self.assertEqual(len(app.get("download_button")), 4)

    def test_filtered_and_empty_views_work_across_all_menus(self):
        app = self.app()
        period = sorted(self.full["Kode_Periode"].unique())[0]
        app.multiselect(key="filter_periods").set_value([period]).run()
        app.multiselect(key="filter_clusters").set_value([0]).run()
        expected = self.full.loc[(self.full["Kode_Periode"] == period) & (self.full["Cluster"] == 0)]
        metric = next(m for m in app.metric if m.label == "Record pada filter")
        self.assertEqual(metric.value, f"{len(expected):,}")
        menus = app.sidebar.radio[0].options
        for menu in menus:
            app.sidebar.radio[0].set_value(menu).run()
            self.assert_no_errors(app)
            self.assertEqual(app.session_state["filter_periods"], [period])
            self.assertEqual(app.session_state["filter_clusters"], [0])
        app.multiselect(key="filter_clusters").set_value([]).run()
        for menu in menus:
            app.sidebar.radio[0].set_value(menu).run()
            self.assert_no_errors(app)
            self.assertTrue(app.info or menu == "Modeling Pipeline")
        app.sidebar.button[0].click().run()
        self.assertEqual(app.session_state["filter_periods"], [])
        self.assertEqual(app.session_state["filter_clusters"], [0, 1, 2, 3])

    def test_source_choices_feature_controls_and_absent_cluster(self):
        app = self.app()
        app.sidebar.radio[0].set_value("Data Understanding").run()
        for source in ("Raw", "Feature Engineering", "Reporting"):
            app.selectbox(key="understanding_source").set_value(source).run()
            self.assert_no_errors(app)
        app.sidebar.radio[0].set_value("EDA Raw Data").run()
        app.selectbox(key="raw_distribution_feature").set_value("TLE_P1").run()
        app.selectbox(key="raw_boxplot_feature").set_value("FD1").run()
        app.multiselect(key="raw_correlation_features").set_value([]).run()
        self.assert_no_errors(app)
        app.sidebar.radio[0].set_value("Feature Engineering Result").run()
        app.selectbox(key="fe_distribution_feature").set_value("Total_LO").run()
        app.multiselect(key="fe_correlation_features").set_value(["Submit_pct"]).run()
        self.assert_no_errors(app)
        app.multiselect(key="filter_clusters").set_value([0]).run()
        app.sidebar.radio[0].set_value("Cluster Interpretation").run()
        app.selectbox(key="interpretation_cluster").set_value(1).run()
        self.assert_no_errors(app)
        self.assertTrue(any("tidak memiliki record" in item.value for item in app.info))

    def test_filters_and_pca_preserve_record_labels_and_coordinates(self):
        before = self.full.copy(deep=True)
        first = self.full.iloc[0]
        filtered = apply_reporting_filters(self.full, periods=[first["Kode_Periode"]],
                                          courses=[first["Kode Mata kuliah"]], classes=[first["Kode Kelas"]], clusters=[0])
        pd.testing.assert_series_equal(filtered["Cluster"], self.full.loc[filtered.index, "Cluster"])
        pd.testing.assert_frame_equal(self.full, before)
        summary = summarize_clusters(filtered)
        self.assertEqual(summary["Record_Count"].sum(), len(filtered))
        self.assertEqual(summary["Cluster"].tolist(), [0, 1, 2, 3])
        empty = apply_reporting_filters(self.full, clusters=[])
        self.assertTrue(empty.empty)
        self.assertEqual(summarize_clusters(empty)["Record_Count"].sum(), 0)
        coords, variance = pca_projection(self.full)
        repeated, repeated_variance = pca_projection(self.full)
        pd.testing.assert_frame_equal(coords.loc[filtered.index], repeated.loc[filtered.index])
        self.assertTrue(np.isfinite(coords.to_numpy()).all())
        self.assertAlmostEqual(variance[0], 0.9772, places=4)
        self.assertEqual(variance, repeated_variance)

    def test_export_csv_excel_match_selection_and_identifier_setting(self):
        subset = self.full.loc[self.full["Cluster"] == 1].copy()
        before = subset.copy(deep=True)
        for include in (False, True):
            with self.subTest(include_identifiers=include):
                payload = export_payloads(subset, include)
                csv = pd.read_csv(BytesIO(payload["dataset"]), dtype=config.IDENTIFIER_DTYPES if include else None)
                expected_columns = list(subset.columns) if include else [c for c in subset if c not in config.IDENTIFIER_COLUMNS]
                self.assertEqual(list(csv.columns), expected_columns)
                self.assertEqual(len(csv), 60)
                self.assertTrue(csv["Cluster"].eq(1).all())
                summary = pd.read_csv(BytesIO(payload["summary"]))
                self.assertEqual(summary["Record_Count"].sum(), 60)
                excel = pd.read_excel(BytesIO(payload["excel"]), sheet_name="Reporting", engine="openpyxl")
                self.assertEqual(list(excel.columns), expected_columns)
                self.assertEqual(len(excel), 60)
                self.assertTrue(excel["Cluster"].eq(1).all())
        pd.testing.assert_frame_equal(subset, before)


if __name__ == "__main__":
    unittest.main()
