# PROJECT PLAN — Dashboard Student Clustering BINUS (Streamlit)

> **Status:** Draft scope v1.0 — 11 Oktober 2026  
> **Fungsi dokumen:** Single source of context untuk pengembangan dashboard clustering mahasiswa berbasis Streamlit.  
> **Catatan penting:** Dokumen ini adalah rancangan scope dan arsitektur dashboard. Dokumen ini **bukan** bukti bahwa notebook, dataset, scaler, model, metrik evaluasi, atau hasil cluster final sudah diverifikasi. Semua nilai bertanda **[PERLU VERIFIKASI]** wajib dicocokkan dengan notebook/model/dataset terbaru sebelum implementasi produksi.

---

## 1. Latar Belakang dan Tujuan

Proyek ini bertujuan membangun dashboard analitik berbasis **Python + Streamlit** untuk menampilkan hasil **student clustering**. Dashboard digunakan untuk memahami pola/karakteristik mahasiswa berdasarkan fitur pembelajaran, aktivitas, evaluasi, dan/atau fitur hasil *feature engineering* yang telah disiapkan.

Dashboard tidak hanya menampilkan hasil cluster, tetapi juga menjelaskan alur analisis dari:

```text
Data asli
↓
EDA data asli
↓
Feature engineering
↓
EDA data hasil feature engineering
↓
Modeling pipeline
↓
Cluster analysis
↓
Cluster interpretation
↓
Download result
```

Tujuan utama MVP dashboard:

- Menampilkan ringkasan dataset, fitur final, metode clustering, scaler, jumlah cluster optimal, dan insight utama.
- Membantu pengguna memahami data asli melalui preview, data dictionary, dan EDA dasar.
- Menjelaskan hasil *feature engineering* dan alasan fitur final dipilih.
- Menampilkan pipeline pembuatan model clustering secara jelas.
- Menampilkan visualisasi hasil clustering dan karakteristik tiap cluster.
- Memberikan interpretasi cluster dalam bentuk insight dan narasi akademik/bisnis.
- Menyediakan output yang bisa diunduh, seperti dataset dengan label cluster dan summary cluster.

**Bukan tujuan MVP tahap awal:** membangun ulang seluruh eksperimen model dari awal, membuat sistem keputusan otomatis individual, atau membuat rekomendasi final yang berdampak langsung pada mahasiswa tanpa validasi akademik dan persetujuan pihak terkait.

---

## 2. Keputusan Scope yang Sudah Dikunci

| Aspek | Keputusan |
| --- | --- |
| Jenis proyek | Dashboard analitik clustering mahasiswa |
| Framework dashboard | **Streamlit** |
| Bahasa utama | **Python** |
| Pola navigasi | **Single-entry app dengan sidebar navigation** |
| Entrypoint utama | `app.py` |
| Struktur UI | Sidebar menu, bukan Streamlit multipage bawaan folder `pages/` |
| Struktur kode | Modular: `sections/` untuk tampilan per menu dan `src/` untuk helper/function reusable |
| Output utama | Dashboard eksplorasi, interpretasi cluster, dan download result |
| Simulasi Class Alert & Recommendation | **Belum masuk MVP utama; menyusul sebagai advanced feature** |

Catatan: jika notebook/model final menunjukkan detail yang berbeda dari dokumen ini, lakukan audit terlebih dahulu dan tandai ketidaksesuaian secara eksplisit sebelum coding dilanjutkan.

---

## 3. MVP Dashboard Clustering — Feature and Scoping

MVP dashboard terdiri dari delapan menu utama di sidebar:

```text
1. Home / Executive Summary
2. Data Understanding
3. EDA Raw Data
4. Feature Engineering Result
5. Modeling Pipeline
6. Cluster Analysis
7. Cluster Interpretation
8. Download Result
```

Setiap menu dirancang sebagai section terpisah di folder `sections/`, tetapi tetap dipanggil dari satu file utama `app.py`.

---

## 4. Home / Executive Summary

### Tujuan

Memberikan gambaran cepat mengenai isi dashboard, dataset, model clustering, dan insight utama.

### Komponen yang ditampilkan

- Total record: **5.725 students**.
- Mahasiswa unik: 583 NIM
- Jumlah fitur final: **8 fitur**.
- Jumlah fitur analisis tambahan: **4 fitur LO**.
- Model Final : **K-Means**
- Scaler: **RobustScaler**
- Jumlah cluster optimal: **4**.
- Silhouette model final K=4: 0,84195
Catatan: K=4 merupakan manual override/final choice, bukan hasil silhouette maksimum otomatis.


### Bentuk tampilan yang disarankan

- KPI cards untuk jumlah data, jumlah fitur final, jumlah cluster, metode, scaler, dan best score.
- Ringkasan pendek mengenai tujuan dashboard.
- 3–5 bullet insight utama setelah hasil cluster final tervalidasi.
- Sidebar summary kecil berisi dataset, fitur final, metode, dan jumlah cluster.

---

## 5. Data Understanding

### Tujuan

Membantu pengguna memahami data asli sebelum proses *feature engineering* dan modeling.

### Komponen yang ditampilkan

- Preview data asli.
- Jumlah baris dan kolom.
- Data dictionary.
- Penjelasan tiap fitur/kolom.
- Makna bisnis/akademik dari tiap kolom.

### Catatan implementasi

- Kolom ID seperti NIM, kode kelas, atau kode mata kuliah harus diperlakukan sebagai identifier, bukan variabel numerik model.
- Jika data mengandung informasi sensitif, versi dashboard publik harus memakai data anonim, sampel tersanitasi, atau agregasi.
- Data dictionary sebaiknya dibuat dalam tabel dengan kolom:

```text
Column Name | Data Type | Description | Example | Academic/Business Meaning | Notes
```

---

## 6. EDA Raw Data

### Tujuan

Menampilkan eksplorasi data asli agar pengguna memahami kualitas, distribusi, dan karakteristik data sebelum proses *feature engineering*.

### Komponen yang ditampilkan

- Shape / dimensi data.
- Tipe data.
- Missing value.
- Duplicate data.
- Statistik deskriptif.
- Distribusi fitur numerik.
- Boxplot / outlier.
- Korelasi.

### Struktur tampilan yang disarankan

Gunakan tab di dalam section EDA agar tidak terlalu panjang:

```text
EDA Raw Data
├── Overview
├── Missing & Duplicate
├── Descriptive Statistics
├── Numerical Distribution
├── Outlier Analysis
└── Correlation Analysis
```

### Catatan implementasi

- Histogram dan boxplot tidak perlu menampilkan semua kolom sekaligus dalam satu layar panjang. Gunakan dropdown/selectbox untuk memilih fitur.
- Korelasi hanya berlaku untuk fitur numerik.
- Jangan membuat klaim kausal dari korelasi.
- Outlier perlu dijelaskan sebagai indikasi data ekstrem, bukan otomatis data salah.

---

## 7. Feature Engineering Result

### Tujuan

Menjelaskan dataset hasil *feature engineering* yang digunakan sebagai dasar analisis/modeling clustering.

### Komponen yang ditampilkan

- Preview dataset hasil feature engineering.
- Daftar fitur final.
- Statistik ringkas fitur final.
- Distribusi fitur final.
- Korelasi antar fitur final.
- Alasan fitur dipilih.

### Fitur final yang direncanakan

Jumlah fitur final dalam scope MVP: **12 fitur** **[JANGAN LUPA VERIFIKASI dengan notebook/model final]**.

Fitur final:

```text
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

Catatan penting:

- Jika model final ternyata hanya menggunakan 8 fitur untuk training clustering, maka dashboard harus membedakan antara:
  - fitur input model clustering, dan
  - fitur analisis/deskriptif pasca-clustering.
- Fitur LO seperti `avg_LO1`, `avg_LO2`, `avg_LO3`, dan `Total_LO` harus diverifikasi apakah digunakan sebagai input model atau hanya untuk analisis deskriptif.
- Jangan memasukkan LO ke model jika keputusan final menyatakan LO hanya untuk analisis setelah cluster terbentuk.

---

## 8. Modeling Pipeline

### Tujuan

Menampilkan diagram/alur mengenai proses pembuatan model agar dashboard mudah dipahami oleh reviewer, dosen, atau pihak akademik.

### Alur konseptual

```text
Raw Data
↓
Data Cleaning
↓
Feature Engineering
↓
Feature Selection
↓
Scaling / Normalization
↓
Clustering Model
↓
Cluster Evaluation
↓
Cluster Interpretation
↓
Dashboard & Recommendation
```

### Komponen yang ditampilkan

- Diagram alur modeling.
- Penjelasan singkat tiap tahap.
- Informasi metode clustering yang digunakan.
- Informasi scaler yang digunakan.
- Informasi jumlah cluster optimal.
- Informasi metrik evaluasi, misalnya Silhouette Score, Davies-Bouldin Index, Calinski-Harabasz Score, atau inertia/elbow jika tersedia.

### Catatan implementasi

- Diagram dapat dibuat dengan `st.graphviz_chart`, Mermaid image, atau komponen visual lain.
- Jangan menampilkan angka evaluasi yang belum diverifikasi dari notebook/model final.
- Jika ada beberapa eksperimen model, tampilkan hanya eksperimen final atau berikan penanda jelas antara eksperimen dan model terpilih.

---

## 9. Cluster Analysis

### Fokus

Visualisasi dan angka.

### Tujuan

Menampilkan hasil clustering dalam bentuk visual dan statistik agar pengguna dapat membandingkan karakteristik tiap cluster.

### Komponen yang ditampilkan

- Jumlah anggota tiap cluster.
- Rata-rata fitur per cluster.
- Heatmap profil cluster.
- Radar chart per cluster.
- PCA / t-SNE / UMAP 2D plot.
- Distribusi fitur berdasarkan cluster.

### Visualisasi yang akan digunakan

```text
Cluster Analysis
├── Cluster Size Bar Chart
├── Cluster Percentage Pie/Donut Chart
├── Mean Feature by Cluster Table
├── Cluster Profile Heatmap
├── Radar Chart per Cluster
├── 2D Projection Plot
└── Feature Distribution by Cluster
```

### Catatan implementasi

- Gunakan label netral `Cluster 0`, `Cluster 1`, dst. sampai interpretasi cluster divalidasi.
- Jangan menganggap nomor cluster sebagai urutan kualitas.
- Jika memakai PCA/t-SNE/UMAP, jelaskan bahwa plot tersebut adalah proyeksi 2D untuk visualisasi, bukan ruang asli model.
- Jika dataset difilter, filter hanya mengubah tampilan/ringkasan, bukan melatih ulang model atau mengubah label cluster.

---

## 10. Cluster Interpretation

### Fokus

Insight dan narasi.

### Tujuan

Mengubah hasil angka/visualisasi cluster menjadi interpretasi yang mudah dipahami secara akademik atau bisnis.

### Komponen yang ditampilkan

- Nama/persona tiap cluster.
- Karakteristik utama tiap cluster.
- Risiko/peluang tiap cluster.
- Kesimpulan bisnis/akademik.

### Format interpretasi yang disarankan

```text
Cluster 0 — [Nama Persona Sementara]
Karakteristik utama:
- ...
- ...

Risiko/peluang:
- ...

Kesimpulan akademik/bisnis:
- ...
```

### Catatan implementasi

- Nama/persona cluster hanya boleh diberikan setelah profil cluster tervalidasi.
- Hindari istilah yang terlalu menghakimi mahasiswa, misalnya “mahasiswa buruk” atau “mahasiswa gagal”.
- Gunakan bahasa netral seperti:
  - “Engagement rendah”
  - “Submission rendah”
  - “Akses materi tinggi”
  - “Performa LO relatif tinggi”
  - “Perlu perhatian akademik”
- Hindari klaim kausal seperti “akses VBL menyebabkan nilai meningkat” kecuali ada desain analisis kausal yang mendukung.

---

## 11. Download Result

### Tujuan

Menyediakan hasil analisis yang dapat diunduh untuk kebutuhan dokumentasi, pelaporan, atau analisis lanjutan.

### Komponen yang ditampilkan

- Download dataset dengan label cluster.
- Download summary cluster.

### Output yang disarankan

```text
1. dataset_with_cluster.csv / .xlsx
   Berisi dataset final + label cluster + cluster persona jika sudah divalidasi.

2. cluster_summary.csv / .xlsx
   Berisi ringkasan jumlah anggota cluster, rata-rata fitur, dan insight ringkas.
```

### Catatan implementasi

- Untuk dashboard publik/demo portfolio, hindari ekspor data individual sensitif.
- Jika ada NIM, nama, kelas, dosen, atau atribut akademik sensitif, lakukan masking/anonymization sesuai kebutuhan.
- Pastikan data yang diunduh diberi keterangan provenance: data asli, hasil feature engineering, hasil clustering, atau hasil simulasi.

---

## 12. Sidebar Navigation Design

Dashboard menggunakan **sidebar navigation**, bukan Streamlit multipage bawaan folder `pages/`.

### Struktur sidebar yang disarankan

```text
Student Clustering Dashboard

Dataset Summary
Rows: 5.725 [PERLU VERIFIKASI]
Final Features: 12 [PERLU VERIFIKASI]
Model: [PERLU VERIFIKASI]
Optimal Cluster: [PERLU VERIFIKASI]

Navigation
○ Home / Executive Summary
○ Data Understanding
○ EDA Raw Data
○ Feature Engineering Result
○ Modeling Pipeline
○ Cluster Analysis
○ Cluster Interpretation
○ Download Result
```

### Prinsip sidebar

- Sidebar menjadi pusat navigasi utama.
- Setiap pilihan sidebar memanggil section berbeda.
- App tetap dijalankan dari satu file utama `app.py`.
- Setiap section disimpan di folder `sections/` dan memiliki fungsi `render()`.
- Subbagian di dalam section dapat menggunakan `st.tabs()`, `st.expander()`, `st.columns()`, atau `st.selectbox()`.

---

## 13. Struktur Folder yang Dikunci untuk MVP

```text
Student_clustering_dashboard/
├── app.py
├── data/
│   ├── raw_data.xlsx
│   └── feature_engineered_data.xlsx
├── models/
│   ├── clustering_model.pkl
│   └── scaler.pkl
├── src/
│   ├── data_loader.py
│   ├── eda_utils.py
│   ├── visualization.py
│   ├── clustering_utils.py
│   └── config.py
├── sections/
│   ├── home.py
│   ├── data_understanding.py
│   ├── eda_raw.py
│   ├── feature_engineering.py
│   ├── modeling_pipeline.py
│   ├── cluster_analysis.py
│   ├── cluster_interpretation.py
│   └── download_result.py
├── requirements.txt
└── README.md
```

### Peran file/folder

| Path | Fungsi |
| --- | --- |
| `app.py` | Entrypoint utama Streamlit, pengatur sidebar, dan router section |
| `data/` | Menyimpan dataset raw dan dataset hasil feature engineering |
| `models/` | Menyimpan model clustering dan scaler yang sudah di-fit |
| `src/config.py` | Konfigurasi path, daftar fitur, nama kolom, label cluster, dan konstanta global |
| `src/data_loader.py` | Fungsi load dataset, cache, dan validasi schema sederhana |
| `src/eda_utils.py` | Fungsi statistik deskriptif, missing value, duplicate, outlier, dan korelasi |
| `src/visualization.py` | Fungsi reusable untuk chart/plot |
| `src/clustering_utils.py` | Fungsi analisis cluster, summary per cluster, load model/scaler jika diperlukan |
| `sections/` | Folder section tampilan dashboard; masing-masing file punya fungsi `render()` |
| `requirements.txt` | Daftar dependency Python |
| `README.md` | Panduan setup, cara menjalankan dashboard, struktur folder, dan batasan project |

---

## 14. Pola Implementasi `app.py`

`app.py` berfungsi sebagai router utama.

Contoh pola implementasi:

```python
import streamlit as st

from sections import (
    home,
    data_understanding,
    eda_raw,
    feature_engineering,
    modeling_pipeline,
    cluster_analysis,
    cluster_interpretation,
    download_result,
)

st.set_page_config(
    page_title="Student Clustering Dashboard",
    layout="wide",
)

st.sidebar.title("Student Clustering Dashboard")

menu = st.sidebar.radio(
    "Navigation",
    [
        "Home / Executive Summary",
        "Data Understanding",
        "EDA Raw Data",
        "Feature Engineering Result",
        "Modeling Pipeline",
        "Cluster Analysis",
        "Cluster Interpretation",
        "Download Result",
    ],
)

if menu == "Home / Executive Summary":
    home.render()
elif menu == "Data Understanding":
    data_understanding.render()
elif menu == "EDA Raw Data":
    eda_raw.render()
elif menu == "Feature Engineering Result":
    feature_engineering.render()
elif menu == "Modeling Pipeline":
    modeling_pipeline.render()
elif menu == "Cluster Analysis":
    cluster_analysis.render()
elif menu == "Cluster Interpretation":
    cluster_interpretation.render()
elif menu == "Download Result":
    download_result.render()
```

---

## 15. Caching dan Performance

Karena Streamlit melakukan rerun script saat ada interaksi widget, loading data dan model harus menggunakan caching.

### Rekomendasi

- Gunakan `@st.cache_data` untuk dataset.
- Gunakan `@st.cache_resource` untuk model/scaler.
- Hindari membaca Excel berulang-ulang di setiap section.
- Hindari menghitung visualisasi berat tanpa cache atau tanpa filter.

Contoh:

```python
@st.cache_data
def load_dataset(path):
    return pd.read_excel(path)

@st.cache_resource
def load_model(path):
    return joblib.load(path)
```

---

## 16. Prinsip Data, Model, dan Interpretasi

- Jangan menukar urutan fitur model.
- Jangan melakukan `fit()` atau `fit_predict()` ulang dari dashboard kecuali memang dibuat sebagai mode eksperimen terpisah.
- Jangan menghitung ulang scaler dari subset data hasil filter.
- Jika model final memakai scaler yang sudah di-fit, gunakan `transform()`, bukan `fit_transform()`.
- Jika label cluster sudah tersedia dari file hasil clustering, dashboard dapat mulai dari mode reporting.
- Jika dashboard menerima data baru, mode inference harus dipisahkan dari mode reporting.
- Cluster bukan label benar/salah, lulus/gagal, atau baik/buruk.
- Interpretasi cluster harus berbasis profil data, bukan asumsi subjektif.
- Semua angka evaluasi model harus berasal dari notebook/model final yang sama.

---

## 17. Mode Produk

Terdapat dua mode produk yang dapat dipilih.

### Mode A — Reporting Dashboard

Dashboard membaca dataset yang sudah memiliki label cluster.

Kelebihan:

- Lebih sederhana.
- Lebih aman untuk MVP.
- Lebih mudah diaudit.
- Cocok untuk portfolio dan presentasi analitik.

### Mode B — Inference Dashboard

Dashboard menerima data baru, melakukan transformasi, scaling, lalu prediksi cluster.

Syarat:

- Feature engineering harus tersedia dan konsisten.
- Scaler sudah di-fit dan tersimpan.
- Model clustering sudah di-fit dan tersimpan.
- Urutan fitur harus sama dengan training.
- Perlu validasi schema input.

### Keputusan MVP

Default MVP menggunakan **Mode A — Reporting Dashboard**. Mode B dapat ditambahkan setelah artefak final, pipeline feature engineering, scaler, dan model dipastikan siap.

---

## 18. Advanced Feature yang Belum Masuk MVP

Fitur berikut belum masuk scope MVP utama dan dapat dikerjakan setelah dashboard dasar stabil:

```text
1. Student Simulation
2. Class Alert
3. Recommendation System
4. Rekomendasi tindakan untuk dosen/prodi
5. Upload dataset baru untuk inference
6. Perbandingan antar kelas/mata kuliah/dosen
7. Export report PDF
```

Catatan khusus:

- “Class Alert” dan “Recommendation” harus menggunakan rule yang jelas dan tidak boleh dibuat seolah-olah keputusan otomatis final.
- Rekomendasi sebaiknya diarahkan sebagai rekomendasi tindakan akademik/intervensi, bukan label permanen terhadap mahasiswa.

---

## 19. Risiko yang Perlu Dijaga

1. **Mismatch fitur final:** scope menyebut 12 fitur, tetapi model final mungkin menggunakan 8 fitur. Harus diverifikasi sebelum coding final.
2. **Preprocessing mismatch:** scaler di dashboard harus sama dengan scaler saat model final dibuat.
3. **Wrong model version:** dataset, model, scaler, label cluster, dan metrik harus berasal dari eksperimen yang sama.
4. **Data leakage:** fitur target/LO tidak boleh masuk ke model jika keputusan final menyatakan LO hanya untuk analisis deskriptif.
5. **Retraining tidak sengaja:** dashboard tidak boleh melatih ulang model saat filter UI berubah.
6. **Misleading interpretation:** cluster bukan kategori kualitas absolut dan tidak boleh dianggap hubungan sebab-akibat.
7. **Data privacy:** data mahasiswa, NIM, kelas, dosen, dan nilai akademik harus diperlakukan sebagai data sensitif.
8. **Data provenance:** bedakan data asli, data hasil feature engineering, data hasil clustering, dan data simulasi.
9. **Granularity:** pastikan apakah satu baris berarti satu mahasiswa, satu mahasiswa-mata kuliah, satu mahasiswa-kelas, atau grain lain.
10. **Overloaded dashboard:** EDA yang terlalu panjang harus dirapikan dengan tabs, dropdown, dan expander.

---

## 20. Tahapan Implementasi yang Disarankan

| Fase | Fokus | Output |
| --- | --- | --- |
| 0. Audit Artefak | Cek dataset raw, dataset FE, notebook, model, scaler, hasil cluster | Model/data manifest |
| 1. Setup Project | Buat struktur folder, environment, requirements | Project Streamlit siap run |
| 2. Data Loading | Implement loader untuk raw dan FE dataset | Dataset berhasil terbaca dengan cache |
| 3. Sidebar & Sections | Implement `app.py` + semua file di `sections/` | Navigasi dashboard berjalan |
| 4. Home & Data Understanding | Implement executive summary dan data dictionary | Halaman awal informatif |
| 5. EDA Raw Data | Implement missing, duplicate, descriptive stats, distribusi, outlier, korelasi | EDA dasar selesai |
| 6. Feature Engineering Result | Tampilkan dataset FE, fitur final, statistik, distribusi, korelasi | FE result jelas |
| 7. Modeling Pipeline | Buat diagram dan narasi pipeline | Alur model mudah dipahami |
| 8. Cluster Analysis | Implement cluster size, profile, heatmap, radar, 2D projection | Visual cluster selesai |
| 9. Cluster Interpretation | Tambahkan persona, insight, risiko/peluang, kesimpulan | Narasi cluster selesai |
| 10. Download Result | Tambahkan download dataset dan summary | Output bisa diekspor |
| 11. QA | Cek angka, filter, cache, error, dan privasi | Dashboard siap demo |

---

## 21. Instruksi untuk Codex / ChatGPT Work

Gunakan instruksi berikut saat mulai coding dengan Codex atau ChatGPT Work:

> Anda bertindak sebagai Senior Python Engineer dan Data/ML Dashboard Engineer. Bangun dashboard Streamlit untuk Student Clustering BINUS berdasarkan `PROJECT_PLAN.md`. Gunakan single-entry app dengan `app.py` sebagai router utama dan sidebar navigation. Jangan gunakan Streamlit multipage folder `pages/`. Pisahkan setiap menu ke folder `sections/` dengan fungsi `render()`. Gunakan folder `src/` untuk helper data loading, EDA, visualisasi, clustering utilities, dan konfigurasi. Gunakan caching untuk load dataset dan model. Jangan mengubah dataset, notebook, model, atau scaler asli. Jangan melakukan retraining dari dashboard. Jika ada informasi model, fitur, scaler, jumlah cluster, atau metrik yang belum terverifikasi, tandai sebagai `[PERLU VERIFIKASI]` dan jangan mengarang angka. Fokus MVP pada Home, Data Understanding, EDA Raw Data, Feature Engineering Result, Modeling Pipeline, Cluster Analysis, Cluster Interpretation, dan Download Result.

---

## 22. Checklist Sebelum Coding Produksi

- [ ] Dataset raw final tersedia.
- [ ] Dataset hasil feature engineering final tersedia.
- [ ] Dataset hasil clustering final tersedia atau pipeline prediksi final tersedia.
- [ ] Jumlah fitur final sudah dipastikan.
- [ ] Daftar fitur final dan urutannya sudah dipastikan.
- [ ] Metode clustering final sudah dipastikan.
- [ ] Scaler final sudah dipastikan.
- [ ] Jumlah cluster optimal sudah dipastikan.
- [ ] Metrik evaluasi final sudah dipastikan.
- [ ] Label/persona cluster sudah divalidasi.
- [ ] Data dictionary tersedia.
- [ ] Aturan privasi/anonymization jelas.
- [ ] Mode dashboard dipilih: Reporting / Inference / keduanya.

---

## 23. Status Penyusunan

Dokumen ini sudah disesuaikan dengan scope MVP terbaru:

- Sidebar navigation.
- `app.py` sebagai router utama.
- `sections/` untuk setiap menu dashboard.
- `src/` untuk helper reusable.
- Delapan menu MVP utama.
- Advanced feature seperti Class Alert dan Recommendation dipisahkan untuk tahap berikutnya.

Update berikutnya dilakukan setelah file final notebook, dataset, scaler, model, dan hasil clustering diverifikasi.
