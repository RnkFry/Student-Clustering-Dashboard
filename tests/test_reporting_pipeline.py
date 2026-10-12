"""Meaningful checks for immutable sources, schema failures, and frozen inference."""

from contextlib import ExitStack
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from src import config
from src.clustering_utils import (
    build_cluster_summary, build_clustered_dataset, load_model_and_scaler,
    predict_clusters, prepare_model_input, save_reporting_artifacts,
    validate_model_artifacts, validate_model_input, validate_project, _publish_reporting_payloads,
)
from src.config import ModelContractError
from src.data_loader import (
    load_feature_engineered_data, load_reporting_data, load_reporting_manifest, validate_fe_schema,
    verify_original_file, verify_originals,
)


class ReportingPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_hashes = verify_originals()
        cls.fe = load_feature_engineered_data()
        cls.scaler, cls.model = load_model_and_scaler()
        cls.clustered = build_clustered_dataset()

    @classmethod
    def tearDownClass(cls):
        if verify_originals() != cls.original_hashes:
            raise AssertionError("Original artifacts changed during testing")

    def test_full_reporting_matches_audit_and_preserves_fe(self):
        result, details = validate_project()
        self.assertEqual(result.shape, (5725, 19))
        self.assertEqual(details["unique_nim_count"], 583)
        self.assertEqual(result["Cluster"].value_counts().to_dict(), config.EXPECTED_CLUSTER_COUNTS)
        np.testing.assert_array_equal(result["Cluster"].to_numpy(), self.model.labels_)
        self.assertNotIn("Cluster", self.fe.columns)
        pd.testing.assert_frame_equal(result.drop(columns="Cluster"), self.fe)

    def test_predict_never_fits_or_mutates_saved_state(self):
        centers = self.model.cluster_centers_.copy()
        saved_labels = self.model.labels_.copy()
        center = self.scaler.center_.copy()
        scale = self.scaler.scale_.copy()
        with ExitStack() as stack:
            for obj, method in (
                (self.scaler, "fit"), (self.scaler, "fit_transform"),
                (self.model, "fit"), (self.model, "fit_predict"),
            ):
                stack.enter_context(patch.object(obj, method, side_effect=AssertionError("Retraining forbidden")))
            labels = predict_clusters(self.fe, self.scaler, self.model)
        np.testing.assert_array_equal(labels, saved_labels)
        np.testing.assert_array_equal(self.model.cluster_centers_, centers)
        np.testing.assert_array_equal(self.scaler.center_, center)
        np.testing.assert_array_equal(self.scaler.scale_, scale)

    def test_missing_model_feature_is_rejected(self):
        with self.assertRaisesRegex(ModelContractError, "VBL_pct"):
            prepare_model_input(self.fe.drop(columns="VBL_pct"))

    def test_exact_model_order_and_count_are_required(self):
        features = self.fe.loc[:, list(config.MODEL_FEATURES)]
        with self.assertRaisesRegex(ModelContractError, "Urutan/jumlah"):
            validate_model_input(features.iloc[:, ::-1])
        with self.assertRaisesRegex(ModelContractError, "Urutan/jumlah"):
            validate_model_input(features.assign(avg_LO1=0))
        # The selector itself restores config order before handing an array to sklearn.
        shuffled = self.fe.iloc[:, ::-1]
        np.testing.assert_array_equal(prepare_model_input(shuffled), prepare_model_input(self.fe))

    def test_nonfinite_values_are_rejected(self):
        for value in (np.nan, np.inf, -np.inf):
            with self.subTest(value=value):
                bad = self.fe.iloc[:2].copy()
                bad["Course_pct"] = bad["Course_pct"].astype(float)
                bad.loc[bad.index[0], "Course_pct"] = value
                with self.assertRaisesRegex(ModelContractError, "NaN/inf"):
                    prepare_model_input(bad)

    def test_text_boolean_empty_and_duplicate_columns_are_rejected(self):
        for value in ("70", True):
            with self.subTest(value=value):
                bad = self.fe.iloc[:2].copy()
                bad["FD_pct"] = value
                with self.assertRaisesRegex(ModelContractError, "numerik"):
                    prepare_model_input(bad)
        with self.assertRaisesRegex(ModelContractError, "kosong"):
            prepare_model_input(self.fe.iloc[:0])
        duplicate = pd.concat([self.fe, self.fe[["FD_pct"]]], axis=1)
        with self.assertRaisesRegex(ModelContractError, "duplikat"):
            prepare_model_input(duplicate)

    def test_lo_values_do_not_enter_prediction(self):
        small = self.fe.iloc[:20].copy()
        labels = predict_clusters(small, self.scaler, self.model)
        small.loc[:, list(config.LO_FEATURES)] = -99999.0
        np.testing.assert_array_equal(predict_clusters(small, self.scaler, self.model), labels)

    def test_wrong_model_dimension_or_k_is_rejected(self):
        bad = deepcopy(self.model)
        bad.n_features_in_ = 12
        with self.assertRaisesRegex(ModelContractError, "wajib 8"):
            validate_model_artifacts(self.scaler, bad)
        bad = deepcopy(self.model)
        bad.n_clusters = 5
        with self.assertRaisesRegex(ModelContractError, "n_clusters"):
            validate_model_artifacts(self.scaler, bad)

    def test_invalid_transform_and_predict_are_rejected(self):
        small = self.fe.iloc[:2]
        with patch.object(self.scaler, "transform", return_value=np.full((2, 8), np.nan)):
            with self.assertRaisesRegex(ModelContractError, "transform"):
                predict_clusters(small, self.scaler, self.model)
        with patch.object(self.model, "predict", return_value=np.array([0, 4])):
            with self.assertRaisesRegex(ModelContractError, "0..3"):
                predict_clusters(small, self.scaler, self.model)

    def test_duplicate_record_keys_are_rejected(self):
        bad = pd.concat([self.fe.iloc[:2], self.fe.iloc[:1]], ignore_index=True)
        with self.assertRaisesRegex(ModelContractError, "kunci record"):
            validate_fe_schema(bad)

    def test_summary_counts_and_external_means(self):
        summary = build_cluster_summary(self.clustered)
        self.assertEqual(summary["Record_Count"].sum(), 5725)
        self.assertAlmostEqual(summary["Record_Percentage"].sum(), 100)
        self.assertEqual(summary["Cluster"].tolist(), [0, 1, 2, 3])
        for column in config.MODEL_FEATURES + config.LO_FEATURES:
            self.assertIn("Mean_" + column, summary)
            np.testing.assert_allclose(
                summary["Mean_" + column], self.clustered.groupby("Cluster")[column].mean()
            )

    def test_hash_mismatch_is_rejected_even_after_first_success(self):
        # Only temporary test sources are mutated, never the original artifacts.
        with tempfile.TemporaryDirectory(prefix="reporting-contract-test-") as directory:
            root = Path(directory).resolve()
            candidate = root / "source.xlsx"
            candidate.write_bytes(b"audited")
            expected = hashlib.sha256(b"audited").hexdigest()
            with patch.object(config, "PROJECT_ROOT", root), patch.object(config, "ORIGINAL_SHA256", {"source.xlsx": expected}):
                self.assertEqual(verify_original_file(candidate), expected)
                candidate.write_bytes(b"changed")
                with self.assertRaisesRegex(ModelContractError, "SHA-256"):
                    verify_original_file(candidate)

    def test_export_rejects_original_destination_without_modification(self):
        before = verify_originals()
        with patch.object(config, "CLUSTERED_DATA_PATH", config.FE_DATA_PATH):
            with self.assertRaisesRegex(ModelContractError, "Path output"):
                save_reporting_artifacts(self.clustered, overwrite=True)
        self.assertEqual(verify_originals(), before)

    def test_export_rejects_forged_cluster_labels(self):
        bad = self.clustered.copy()
        bad.loc[0, "Cluster"] = 1 if bad.loc[0, "Cluster"] != 1 else 0
        with self.assertRaisesRegex(ModelContractError, "hasil prediksi"):
            save_reporting_artifacts(bad)

    def test_staged_export_publishes_complete_files_and_cleans_staging(self):
        with tempfile.TemporaryDirectory(prefix="reporting-publish-test-") as directory:
            root = Path(directory)
            dataset = root / "clustered_data.csv"
            manifest = root / "reporting_manifest.json"
            dataset.write_bytes(b"old")
            payloads = {dataset: b"new-data", manifest: b'{"valid": true}'}
            with patch.object(config, "PROCESSED_DIR", root):
                _publish_reporting_payloads(payloads)
            for path, payload in payloads.items():
                self.assertEqual(path.read_bytes(), payload)
            self.assertEqual(set(root.iterdir()), set(payloads))

    @unittest.skipUnless(os.name == "nt", "Windows ACL regression")
    def test_windows_published_file_inherits_parent_permissions(self):
        with tempfile.TemporaryDirectory(prefix="reporting-acl-test-") as directory:
            root = Path(directory)
            target = root / "reporting_manifest.json"
            with patch.object(config, "PROCESSED_DIR", root):
                _publish_reporting_payloads({target: b"{}"})
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                 "(Get-Acl -LiteralPath $env:REPORTING_TEST_TARGET).AreAccessRulesProtected"],
                env={**os.environ, "REPORTING_TEST_TARGET": str(target)},
                capture_output=True, text=True, check=True,
            )
            self.assertEqual(result.stdout.strip(), "False", "Export must inherit the folder ACL")

    def test_permission_error_is_reported_as_access_problem(self):
        denied = PermissionError(13, "Permission denied", str(config.REPORTING_MANIFEST_PATH))
        with patch.object(Path, "read_text", side_effect=denied):
            with self.assertRaisesRegex(ModelContractError, "Izin baca ditolak"):
                load_reporting_manifest()

    @unittest.skipUnless(config.REPORTING_MANIFEST_PATH.exists(), "Run --export for CSV round-trip checks")
    def test_saved_csv_round_trip_and_no_default_overwrite(self):
        saved = load_reporting_data()
        pd.testing.assert_frame_equal(saved, self.clustered, check_exact=False, rtol=1e-12, atol=1e-12)
        with self.assertRaisesRegex(ModelContractError, "sudah tersedia"):
            save_reporting_artifacts(self.clustered)


if __name__ == "__main__":
    unittest.main()
