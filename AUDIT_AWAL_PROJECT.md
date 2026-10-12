**Audit awal Student Clustering Dashboard — 11 Oktober 2026**

Audit selesai. Model dan scaler dapat dimuat, dan dataset FE konsisten dengan keduanya pada pengujian prediksi. Ada potensi mismatch raw → FE pada `Ketepatan_pct` yang perlu ditelusuri sebelum menganggap raw dan FE berasal dari pipeline yang sama. Dashboard belum dibuat.

Audit membaca workbook dan isi/hasil tersimpan notebook, memuat artefak melalui `joblib.load()`, lalu menjalankan `scaler.transform()` dan `model.predict()`. Tidak menjalankan notebook, tidak melatih ulang model, dan tidak melakukan fit ulang scaler. Hash SHA-256 keenam file asli sebelum dan sesudah pemeriksaan identik.

Bukti terstruktur tersedia di [audit/artifact_manifest.json](audit/artifact_manifest.json). Skrip audit yang dapat dijalankan ulang tersedia di [audit/inspect_artifacts.py](audit/inspect_artifacts.py). Keduanya hanya merupakan artefak audit tambahan.

**1. Struktur aktual dan arahan utama dokumen .md**

File yang ditemukan:

```text
PROJECT_PLAN_DASHBOARD_STREAMLIT_BINUS_REVISED.md
data/raw_data.xlsx
data/feature_engineered_data.xlsx
models/clustering_model.pkl
models/scaler.pkl
notebooks/KMeans_Student_Clustering_8F_Dataset_V3.ipynb
```

`notebooks/Clustering_Student_Analysis.ipynb` yang disebut dalam permintaan tidak tersedia. Audit memakai notebook aktual di atas. Belum ada `app.py`, `src/`, `sections/`, `requirements.txt`, atau `README.md` pada struktur awal.

Dokumen merupakan draft scope v1.0, bukan bukti final hasil modeling. Arahan utamanya:

- Python + Streamlit, satu entrypoint `app.py`, navigasi sidebar.
- Kode modular: `sections/` untuk setiap menu dengan fungsi `render()`, `src/` untuk helper.
- Delapan menu MVP: Home / Executive Summary, Data Understanding, EDA Raw Data, Feature Engineering Result, Modeling Pipeline, Cluster Analysis, Cluster Interpretation, Download Result.
- Default produk: Mode A / Reporting Dashboard. Inference data baru merupakan pengembangan berikutnya setelah pipeline tervalidasi.
- Cache dataset melalui `st.cache_data`, model/scaler melalui `st.cache_resource`.
- Pertahankan urutan fitur; gunakan scaler tersimpan melalui `transform()`; jangan retraining ketika pengguna memfilter data.
- Angka bertanda `[PERLU VERIFIKASI]` harus diganti berdasarkan artefak yang sama. Pisahkan fitur model dari fitur analisis LO.
- Validasi persona cluster, jelaskan proyeksi 2D sebagai visualisasi, hindari klaim kausal, dan perhatikan anonimisasi data mahasiswa.
- Student Simulation, Class Alert, Recommendation System, upload inference, dan ekspor PDF belum termasuk MVP.

Referensi `PROJECT_PLAN.md` dalam contoh instruksi dokumen berbeda dari nama file aktual. Untuk pekerjaan berikutnya, gunakan nama file aktual di atas.

**2. Kolom raw_data.xlsx**

Sheet: `Sheet1`. Ukuran: **5.725 baris × 103 kolom**. Nama kolom berikut ditulis sesuai urutan asli; spasi dan kapitalisasi perlu dipertahankan.

```text
Kode_Periode, Kode Kelas, Kode Dosen, Kode Mata kuliah, Mata kuliah, NIM,
TP1_LO1, TP1_LO2, TP1_LO3, TP1_Total,
TP2_LO1, TP2_LO2, TP2_LO3, TP2_Total,
TK1_LO1, TK1_LO2, TK1_LO3, TK1_Total,
TK2_LO1, TK2_LO2, TK2_LO3, TK2_Total,
TK3_LO1, TK3_LO2, TK3_LO3, TK3_Total,
TK4_LO1, TK4_LO2, TK4_LO3, TK4_Total,
Quiz1_LO1, Quiz1_LO2, Quiz1_LO3, Quiz1_Total,
Quiz2_LO1, Quiz2_LO2, Quiz2_LO3, Quiz2_Total,
Final_Exam_LO1, Final_Exam_LO2, Final_Exam_LO3, Final_Exam_Total,
TLE_P1, TLE_P2, TLE_P3, TLE_P4, TLE_P5, TLE_P6, TLE_P7, TLE_P8, TLE_P9,
FD1, FD2, FD3, FD4, FD5, FD6, FD7, FD8, FD9, FD10,
LN1, LN2, LN3, LN4, LN5, LN6, LN7, LN8, LN9, LN10,
PPT1, PPT2, PPT3, PPT4, PPT5, PPT6, PPT7, PPT8, PPT9, PPT10,
VBL1, VBL2, VBL3, VBL4, VBL5, VBL6, VBL7, VBL8, VBL9, VBL10,
Timestamp_TP1, Timestamp_TP2, Timestamp_TK1, Timestamp_TK2, Timestamp_TK3, Timestamp_TK4,
Deadline_TP1, Deadline_TP2, Deadline_TK1, Deadline_TK2, Deadline_TK3, Deadline_TK4
```

Ada **583 NIM unik**, 79 kode kelas unik, 33 kode mata kuliah unik, dan 270 kombinasi periode–mata kuliah–kelas. Tidak ada duplikasi seluruh baris maupun duplikasi kunci `(Kode_Periode, Kode Mata kuliah, Kode Kelas, NIM)`. Dengan demikian, 5.725 adalah jumlah record mahasiswa dalam konteks periode–mata kuliah–kelas, bukan jumlah mahasiswa unik.

Missing value hanya ditemukan pada timestamp pengumpulan:

| Kolom | Missing |
| --- | ---: |
| Timestamp_TP1 | 438 |
| Timestamp_TP2 | 523 |
| Timestamp_TK1 | 97 |
| Timestamp_TK2 | 116 |
| Timestamp_TK3 | 127 |
| Timestamp_TK4 | 176 |

Total 1.477 sel missing. Seluruh deadline terisi. Missing timestamp cocok secara numerik dengan perhitungan jumlah tugas yang tidak dikumpulkan untuk `Submit_pct`; jangan langsung menganggapnya perlu imputasi.

Dalam pembacaan pandas, NIM dan periode bertipe integer; kode/nama bertipe string; nilai assessment dan akses materi bertipe integer; TLE bertipe float; timestamp/deadline bertipe datetime. NIM dan kode tetap identifier, bukan fitur clustering. Rincian dtype setiap kolom ada pada manifest.

**3. Kolom feature_engineered_data.xlsx**

Sheet: **`Fitur_Clustering`**. Ukuran: **5.725 baris × 18 kolom**.

```text
Kode_Periode
Kode Kelas
Kode Dosen
Kode Mata kuliah
Mata kuliah
NIM
Course_pct
Dosen_pct
FD_pct
PPT_pct
LN_pct
VBL_pct
Submit_pct
Ketepatan_pct
avg_LO1
avg_LO2
avg_LO3
Total_LO
```

Komposisi: 6 identifier + 8 fitur input clustering + 4 fitur LO untuk analisis eksternal. Tidak ada kolom `Cluster` atau persona cluster. Tidak ada missing value atau duplikasi seluruh baris. Keenam identifier sama persis dengan raw data, termasuk urutan seluruh baris.

Seluruh 12 fitur analisis numerik. Delapan fitur input model terisi, finite, dan berada pada rentang 0–100. `Total_LO = avg_LO1 + avg_LO2 + avg_LO3` cocok persis pada seluruh baris.

**4. Fitur final model clustering**

Konfigurasi aktif notebook adalah **F8 + ROBUST + K_OVERRIDE=4**. Urutan input wajib:

```python
[
    "Course_pct",
    "Dosen_pct",
    "FD_pct",
    "PPT_pct",
    "LN_pct",
    "VBL_pct",
    "Submit_pct",
    "Ketepatan_pct",
]
```

`avg_LO1`, `avg_LO2`, `avg_LO3`, dan `Total_LO` tidak digunakan sebagai input model final. Notebook menjadikannya external profile/outcome setelah cluster terbentuk. Jumlah 12 dalam scope sebaiknya dimaknai sebagai fitur analisis tersedia; jumlah input model adalah 8.

Model dan scaler sama-sama memiliki `n_features_in_=8`. Keduanya tidak menyimpan `feature_names_in_` karena notebook melakukan training dari array NumPy. Nama dan urutan fitur didapat dari konfigurasi notebook, lalu diperkuat dengan kecocokan median/IQR scaler, seluruh label prediksi, centroid, dan metrik. Mengandalkan jumlah kolom saja tidak cukup untuk menjaga urutan input.

**5. Hasil load dan pengujian model/scaler**

Keduanya **berhasil dimuat melalui `joblib.load()` tanpa warning** pada environment proyek yang sudah tersedia. Ekstensi `.pkl` ini merupakan artefak yang disimpan notebook menggunakan `joblib.dump()`.

| Artefak | Hasil terverifikasi |
| --- | --- |
| clustering_model.pkl | `sklearn.cluster.KMeans`, sudah di-fit, 4 cluster, 8 fitur |
| scaler.pkl | `sklearn.preprocessing.RobustScaler`, sudah di-fit, 8 fitur |
| Versi sklearn tersimpan | 1.9.0 pada kedua artefak |
| Parameter K-Means | `random_state=42`, `n_init=30`, `max_iter=500`, `init='k-means++'`, `algorithm='lloyd'` |
| Parameter RobustScaler | `quantile_range=(25,75)`, centering/scaling aktif, `unit_variance=False` |

Uji `FE[F8] → scaler.transform() → model.predict()` menghasilkan matriks 5.725 × 8 yang seluruhnya finite. **Seluruh 5.725 prediksi sama persis dengan `model.labels_`**, tanpa perbedaan label maupun urutan baris. Median dan IQR dataset cocok persis dengan parameter scaler, setelah penanganan IQR nol. Perbedaan maksimum centroid dari rata-rata empiris di ruang scaling hanya sekitar `4,62e-14`.

Distribusi cluster cocok dengan output notebook:

| Cluster | Jumlah record | Persentase |
| --- | ---: | ---: |
| 0 | 4.820 | 84,19% |
| 1 | 60 | 1,05% |
| 2 | 559 | 9,76% |
| 3 | 286 | 5,00% |

Metrik dihitung ulang menggunakan scaler dan model tersimpan, tanpa retraining:

| Metrik | Nilai audit | Output notebook |
| --- | ---: | ---: |
| Silhouette | 0,841954598 | 0,84195 |
| Davies-Bouldin | 0,340715690 | 0,34072 |
| Calinski-Harabasz | 36.864,558669 | 36.864,56 |
| Inertia | 42.983,126581 | 42.983,13 |

Ini memberi bukti kuat konsistensi FE–scaler–model–hasil notebook, tetapi tidak membuktikan seluruh riwayat pembuatan raw → FE.

**6. Library Python yang dibutuhkan**

Python aktif bawaan adalah 3.13.13 di `C:\Users\alifa\AppData\Local\Programs\Python\Python313\python.exe`. Environment ini memiliki pandas/NumPy, tetapi belum memiliki openpyxl, scikit-learn, SciPy, dan joblib sehingga belum siap membaca Excel dan memuat model.

Audit berhasil menggunakan environment yang sudah ada, tanpa instalasi tambahan:

```text
D:\Binus_Adhit_V1\Binus-Project\Binus-Project-Venv\Scripts\python.exe
```

| Package | Versi environment audit | Kebutuhan |
| --- | --- | --- |
| pandas | 3.0.5 | Baca/olah dataset |
| numpy | 2.4.6 | Array dan operasi numerik |
| openpyxl | 3.1.5 | Baca/tulis `.xlsx`; dipakai export notebook |
| scikit-learn | **1.9.0** | Model/scaler, prediksi, evaluasi, PCA/t-SNE |
| scipy | 1.18.0 | Dependency sklearn; Hungarian matching notebook |
| joblib | 1.5.3 | Load artefak model/scaler |
| threadpoolctl | 3.6.0 | Dependency sklearn; membatasi thread saat audit |
| matplotlib | 3.11.0 | Visualisasi notebook |
| seaborn | 0.13.2 | Visualisasi notebook |
| ipython | 9.15.0 | `display()` dan `FileLink()` notebook |
| ipykernel | 7.3.0 | Menjalankan notebook dengan kernel Python |
| statsmodels | 0.14.6 | OLS, VIF, dan koreksi FDR pada cell analisis LO |
| umap-learn | 0.5.12 | Opsional: proyeksi UMAP; notebook punya fallback t-SNE |
| streamlit | 1.59.0 | Dibutuhkan pada tahap dashboard berikutnya |
| plotly | Belum terpasang | Opsional jika visual dashboard memakai Plotly |

Numba dan pynndescent tersedia sebagai dependency UMAP. `pathlib`, `warnings`, `json`, `ast`, dan `hashlib` berasal dari standard library, bukan paket pip terpisah. Tidak ada library tambahan yang dipasang selama audit dan belum dibuat `requirements.txt` produksi.

Untuk reproduksi load yang sudah berhasil, gunakan environment di atas dan pertahankan scikit-learn 1.9.0. Daftar versi ini mendokumentasikan hasil lokal yang teruji, bukan klaim kompatibilitas dengan semua versi lain. Seluruh notebook belum dijalankan ulang; keberadaan paket berbeda dari verifikasi eksekusi notebook lengkap.

**7. Potensi mismatch dan hal yang perlu dituntaskan**

| Temuan | Bukti dan implikasi |
| --- | --- |
| Raw → FE: `Ketepatan_pct` belum konsisten dengan kandidat rumus timestamp/deadline | Rumus `jumlah Timestamp <= Deadline / 6 × 100` berbeda dari FE pada **1.886 dari 5.725 baris (32,94%)**, dengan selisih maksimum **83,33 poin persentase**. Membandingkan tanggal tanpa jam tetap menghasilkan 1.886 mismatch. Di raw, tidak ada timestamp terisi yang melewati deadline. Perlu konfirmasi definisi ketepatan waktu dan provenance timestamp/deadline sebelum mengklaim FE dibuat dari raw ini. |
| Pipeline FE asli tidak tersedia di notebook clustering | Notebook langsung membaca dataset FE. Rumus resmi `Course_pct`, `Dosen_pct`, dan `Ketepatan_pct` belum dapat ditelusuri dari kode yang tersedia. Kecocokan identifier tidak membuktikan kesamaan semua sumber fitur. |
| Scope 12 fitur versus model 8 fitur | Gunakan F8 untuk input; 4 LO hanya untuk analisis eksternal. Memasukkan 12 fitur akan salah secara schema dan metodologi. |
| Scope menyebut 5.725 students | Terdapat 583 NIM unik. Bedakan jumlah record dari jumlah mahasiswa unik. |
| Jumlah cluster bukan hasil maksimum silhouette | Model final memakai `MANUAL_OVERRIDE`, K=4. Output notebook menunjukkan AUTO_K combined=5 dan silhouette terbaik pada K=6 sebesar 0,85146. Nilai 0,84195 adalah silhouette model final K=4; jangan menyebut 4 sebagai optimum otomatis atau memasang score K=6 untuk model K=4. |
| IQR nol pada `Submit_pct` | Q1=Q3=100, sehingga scaler tersimpan memakai `scale_=1`. Hasil scaling fitur ini berada pada -100 hingga 0, dengan simpangan baku sekitar 12,18; fitur lain sekitar 0,58–1,00. Ini berpotensi membuat jarak clustering didominasi submission. Output PCA notebook menunjukkan PC1 97,72% dengan loading Submit_pct 0,9973. Silhouette tinggi perlu dibaca dalam konteks ini. |
| Cluster sangat tidak seimbang | Cluster 0 berisi 84,19% record, cluster 1 hanya 1,05%. Kualitas interpretasi tidak bisa dinilai dari silhouette saja. |
| Nama/urutan fitur tidak melekat di artefak | Model/scaler tidak memiliki `feature_names_in_`. Daftar dan urutan F8 harus dikunci dalam manifest/config pada tahap implementasi. |
| Notebook memakai path dataset eksternal | Konfigurasi menunjuk `Folder-Clustering\Feature Engineering\Hasil Feature Engineering\Dataset_Student_Clustering_V3.xlsx`, lalu fallback file lokal bernama sama. Notebook belum menunjuk `data/feature_engineered_data.xlsx`; rerun di folder ini bergantung pada path eksternal. |
| Nama notebook berbeda dari permintaan | File aktual `KMeans_Student_Clustering_8F_Dataset_V3.ipynb`; tidak ada `Clustering_Student_Analysis.ipynb`. |
| Dokumentasi notebook tertinggal dari kode | Markdown menyebut 7 preprocessing/35 kombinasi, sementara kode memuat 8 termasuk ROBUST: 5 × 8 = **40 kombinasi**. |
| Reporting dataset belum memuat label | FE tidak memiliki `Cluster`. Label tersedia pada model dan berhasil direproduksi. Untuk reporting berikutnya, buat hasil berlabel sebagai artefak turunan dengan provenance; pertahankan dataset asli. |
| StandardScaler tambahan di notebook | StandardScaler pada analisis regresi LO digunakan untuk koefisien regresi, terpisah dari RobustScaler clustering. Jangan tertukar saat menyiapkan pipeline dashboard. |
| Reproduksibilitas environment | Python bawaan dan venv memiliki paket berbeda. Model/scaler dimuat dan diuji menggunakan venv dengan sklearn 1.9.0. |

Pemeriksaan hubungan raw → FE tambahan:

- `FD_pct`, `PPT_pct`, `LN_pct`, dan `VBL_pct` cocok persis dengan rata-rata sepuluh kolom biner masing-masing × 100.
- `avg_LO1/2/3` cocok persis dengan rata-rata sembilan assessment masing-masing LO: TP1, TP2, TK1–TK4, Quiz1, Quiz2, Final_Exam.
- `Submit_pct` cocok dengan jumlah enam timestamp pengumpulan yang terisi / 6 × 100, dengan selisih numerik maksimum sekitar `3,55e-15`.
- `Total_LO` cocok persis dengan jumlah tiga rata-rata LO.
- Semua rumus di atas merupakan kandidat yang dicocokkan secara numerik; notebook ini tidak menyediakan implementasi FE asli.

Tidak ada error output tersimpan pada notebook. Warning tersimpan untuk UMAP terkait progress widget dan pengaturan thread tidak menunjukkan kegagalan model. Pengujian ulang stability, UMAP, regresi LO, dan pemilihan K tidak dilakukan dalam audit ini; angka-angka tersebut tetap bersumber dari hasil notebook tersimpan.

Langkah berikutnya yang perlu diselesaikan sebelum implementasi: telusuri mismatch `Ketepatan_pct` ke rumus FE atau versi raw timestamp/deadline, gunakan manifest F8/RobustScaler/K=4 sebagai kontrak model, dan siapkan artefak reporting berlabel yang terpisah beserta definisi fitur/persona. Audit ini tidak mengubah keputusan model maupun file asli.
