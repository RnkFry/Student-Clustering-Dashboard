**Student Clustering BINUS — MVP UI Streamlit**

Sumber utama: [AUDIT_AWAL_PROJECT.md](AUDIT_AWAL_PROJECT.md). Dashboard menyediakan sembilan menu (delapan menu MVP dan Rekomendasi Strategis Prodi) melalui satu `app.py` dan navigasi `st.sidebar.radio`, tanpa folder `pages/`. UI membaca label dari reporting tersimpan; proses pembuatan reporting tetap terpisah melalui CLI dengan RobustScaler dan K-Means K=4.

**Kontrak model**

- Input berurutan: `Course_pct`, `Dosen_pct`, `FD_pct`, `PPT_pct`, `LN_pct`, `VBL_pct`, `Submit_pct`, `Ketepatan_pct`.
- `avg_LO1`, `avg_LO2`, `avg_LO3`, `Total_LO` hanya untuk analisis eksternal.
- Model: K-Means, 4 cluster, K dipilih manual, `random_state=42`, `n_init=30`, `max_iter=500`.
- Scaler: RobustScaler, IQR 25–75, artefak yang sudah di-fit.
- Versi scikit-learn: **1.9.0**, sama dengan artefak audit.
- Sumber final: 5.725 record dan 583 NIM unik. Nomor cluster adalah label netral.

Konfigurasi eksplisit tersimpan di [src/config.py](src/config.py). Nama/urutan fitur tidak tersimpan pada model asli, sehingga kontrak config wajib dipertahankan. Hash kedua dataset, model, scaler, dan notebook dikunci terhadap audit; mengganti salah satu artefak ini memerlukan audit dan kontrak baru. Dokumen rencana sudah diperbarui sejak audit; hash dokumentasi dicatat terpisah dari kontrak artefak ML. Dokumen rencana tidak diubah oleh implementasi ini.

**Struktur proyek**

```text
app.py
src/
  __init__.py
  config.py
  data_loader.py
  clustering_utils.py
  eda_utils.py
  visualization.py
  ui_utils.py
sections/
  __init__.py
  home.py
  data_understanding.py
  eda_raw.py
  feature_engineering.py
  modeling_pipeline.py
  cluster_analysis.py
  cluster_interpretation.py
  download_result.py
data/
  raw_data.xlsx                         # asli, hanya dibaca
  feature_engineered_data.xlsx          # asli, hanya dibaca
  processed/
    clustered_data.csv                 # FE + Cluster
    cluster_summary.csv                # ringkasan cluster
    reporting_manifest.json            # kontrak, hash, provenance, keterbatasan
models/                                # artefak asli, hanya dibaca
notebooks/                             # notebook asli, tidak dijalankan/diubah
tests/test_reporting_pipeline.py
tests/test_mvp_ui.py
requirements.txt
README.md
```

**Environment dan perintah PowerShell**

Jalankan dari folder proyek. Environment audit yang sudah tersedia menggunakan Python 3.13.13:

```powershell
$projectPython = 'D:\Binus_Adhit_V1\Binus-Project\Binus-Project-Venv\Scripts\python.exe'
```

Jika ingin membuat environment lokal baru:

```powershell
python -m venv .venv
$projectPython = '.\.venv\Scripts\python.exe'
& $projectPython -m pip install -r requirements.txt
```

Validasi sumber, schema, urutan/dimensi fitur, tipe numerik, nilai finite, model/scaler, kecocokan label dan distribusi cluster terhadap audit:

```powershell
& $projectPython -B -m src.clustering_utils --validate-only
```

Perintah ini tidak menulis artefak. Jika reporting sudah tersedia, validasi juga memeriksa hash kedua CSV, isi dataset, dan summary. Exit code 0 berarti lolos; exit code 1 disertai `VALIDASI GAGAL: ...` berarti pipeline berhenti. Warning Streamlit terkait cache/runtime ketika menjalankan CLI di luar server tidak mengubah hasil validasi.

Membuat reporting baru secara eksplisit:

```powershell
& $projectPython -B -m src.clustering_utils --export
```

Jika file turunan sudah tersedia, export menolak overwrite secara default. Penggantian **hanya artefak turunan** dapat dilakukan dengan:

```powershell
& $projectPython -B -m src.clustering_utils --export --overwrite
```

Sumber yang gagal kontrak atau reporting yang sudah ada tetapi rusak harus diperiksa terlebih dahulu; CLI berhenti pada mismatch, termasuk sebelum overwrite. Tidak ada opsi untuk menulis dataset/model/scaler/notebook asli.

Uji regresi validasi dan proteksi file:

```powershell
& $projectPython -B -m unittest discover -s tests -v
```

Menjalankan MVP Streamlit:

```powershell
& $projectPython -B -m streamlit run app.py --server.address 127.0.0.1
```

Buka `http://localhost:8501`. Jalankan export terlebih dahulu jika reporting belum tersedia. Rerun Streamlit hanya membaca artefak dan membentuk visual/unduhan dalam memori; pembuatan CSV lokal dilakukan lewat CLI.

**Menu MVP**

| Menu | Konten |
| --- | --- |
| Home / Executive Summary | KPI record dan NIM unik, metadata/metrik model final, distribusi cluster, keterbatasan |
| Data Understanding | Pilihan raw/FE/reporting, preview dan data dictionary dengan definisi yang belum terverifikasi ditandai |
| EDA Raw Data | Overview, tipe data, missing/duplicate, statistik, histogram, boxplot/IQR, korelasi numerik |
| Feature Engineering Result | Pemisahan delapan input dan empat LO, preview, statistik, distribusi dan korelasi |
| Modeling Pipeline | Alur reporting, metadata, urutan input, parameter scaler dan centroid global |
| Cluster Analysis | Jumlah/persentase record, NIM unik per cluster, tabel/heatmap rata-rata, radar, PCA 2D dan boxplot |
| Cluster Interpretation | Label sementara Cluster 0–3, profil deskriptif dan perbandingan dengan seluruh reporting |
| Rekomendasi Strategis Prodi | Nama profil, karakteristik dan rekomendasi dari Excel; delapan fitur serta LO aktual dibandingkan dengan cluster global |
| Download Result | CSV dataset/summary, Excel dua sheet, JSON provenance; mengikuti filter aktif |

Filter periode, mata kuliah, kelas, dan cluster berlaku pada seluruh menu. Pilihan kosong pada periode/mata kuliah/kelas berarti semua; mengosongkan pilihan cluster berarti tidak ada record. Kombinasi filter tanpa hasil ditampilkan sebagai pesan informatif. Reset filter mengembalikan seluruh reporting. Raw/FE mengikuti record yang sama melalui alignment identifier dengan reporting.

Filter hanya memilih baris: label cluster tidak diprediksi ulang. Jumlah record dan NIM unik ditampilkan terpisah; satu NIM dapat muncul pada beberapa cluster melalui record berbeda. Metrik model dan centroid pada Modeling Pipeline merupakan hasil global audit dan tetap ketika filter berubah. Rata-rata/distribusi cluster mengikuti filter.

PCA dihitung menggunakan SVD pada seluruh matriks delapan fitur setelah `scaler.transform()`, lalu hanya titik yang dipilih filter yang ditampilkan. PCA bukan training ulang clustering; koordinat dan label tetap. Pilihan batas titik mengambil sampel deterministik untuk plot saja. Radar memakai persentase asli 0–100. Chart menggunakan Vega-Lite bawaan Streamlit, tanpa dependency runtime tambahan.

Ekspor dataset secara default menghapus enam kolom identifier; checkbox dapat menyertakannya untuk penggunaan lokal. Penghapusan identifier belum menjamin anonimisasi penuh. NIM unik pada summary dihitung sebelum identifier dihapus. CSV/Excel/JSON dibentuk dalam memori dan tidak menimpa artefak reporting atau sumber. Provenance JSON mencatat sumber reporting dan filter. Nama/persona interpretatif final belum ditetapkan; profil LO dijelaskan sebagai asosiasi deskriptif.

Pengujian tambahan memakai Streamlit AppTest untuk sembilan menu, filter dan reset, hasil kosong, pilihan dataset/fitur, schema chart Vega-Lite, dan kesesuaian ekspor. Pengujian menolak panggilan `fit`, `fit_transform`, `fit_predict`, dan `KMeans.predict` dari UI, serta memeriksa bahwa sumber/reporting lokal tetap utuh. Pemeriksaan ini tidak mencakup penilaian visual piksel di browser.

**Rekomendasi Strategis Prodi**

Pilih menu **Rekomendasi Strategis Prodi**, lalu pilih Cluster 0–3. Sumber teks adalah `data/reference/Rekomendasi Prodi.xlsx`, sheet `Sheet1`. Header aktual berada di B9:D9 dan empat mapping di B10:D13. Nama profil dan ID diverifikasi terhadap `docs/FEATURE_REKOMENDASI_PRODI.md`. Hasil inspeksi dan pencocokan model dicatat di [docs/REKOMENDASI_PRODI_VALIDATION.md](docs/REKOMENDASI_PRODI_VALIDATION.md).

Implementasi terpisah menjadi `src/recommendation_loader.py` (pandas/openpyxl, schema, identitas, duplicate/missing/unknown mapping, cache berdasarkan isi workbook), `src/recommendation_service.py` (lookup ID final dan agregasi data aktual), dan `sections/recommendation.py` (UI). Path workbook dibentuk dari project root. Tidak ada dependency tambahan, teks rekomendasi hardcoded, prediksi ulang, atau perubahan model/scaler.

Teks karakteristik dan rekomendasi dipertahankan dari Excel termasuk baris baru. Filter hanya memengaruhi statistik; profil acuan Excel tetap berasal dari cluster global. Tabel dan chart membandingkan rata-rata filter dengan rata-rata cluster yang sama pada seluruh reporting. LO adalah profil eksternal, bukan input clustering; chart LO memakai nilai asli, bukan persentase target. Jumlah record dan NIM unik dibedakan. Jika cluster tidak memiliki record pada filter, pesan kosong ditampilkan dan teks acuan Excel tetap tersedia tanpa statistik pengganti.

Workbook yang hilang/rusak, schema salah, sel wajib kosong, mapping duplikat/tidak lengkap, ID di luar 0–3, atau nama profil yang tertukar menghentikan modul rekomendasi dengan error informatif. Perubahan isi workbook membatalkan cache. Service menandai fitur/LO yang hilang atau tidak valid tanpa mengisi nilai pengganti; kontrak loader reporting existing tetap menolak file reporting rusak/tidak sesuai audit sebelum masuk modul. Koreksi data sumber harus melalui proses audit existing.

Pengujian khusus fitur:

```powershell
& $projectPython -B -m unittest discover -s tests -p 'test_recommendation.py' -v
```

Pengujian mencakup kesamaan teks dengan workbook, mapping 0–3, urutan baris, kesalahan schema/mapping, invalidasi cache, agregasi filter, LO eksternal, data tidak lengkap, error/empty state UI, dan integrasi empat pilihan cluster. Jalankan seluruh regresi dengan perintah `unittest discover -s tests -v` di atas. Nama profil Excel hanya diperkenalkan pada modul rekomendasi; modul interpretasi MVP tetap memakai label netral existing.

**Validasi dan alur data**

`load_feature_engineered_data()` membaca sheet `Fitur_Clustering` memakai `st.cache_data`. Raw dan FE tetap terpisah. Cache memasukkan SHA-256 sebagai key agar penggantian file tidak tersamarkan cache lama. Identifier dibaca sebagai string untuk menghindari perlakuan sebagai besaran numerik.

`load_model_and_scaler()` memakai `st.cache_resource`, memeriksa hash dan versi sklearn, lalu memastikan artefak fitted berjenis RobustScaler/KMeans dengan delapan fitur dan parameter audit. `prepare_model_input()` mengambil delapan kolom mengikuti config. `validate_model_input()` menolak urutan salah, dimensi salah, missing fitur, teks/boolean, NaN, dan inf. Setelah `transform()`, shape dan nilai finite kembali diperiksa sebelum `predict()`.

`build_clustered_dataset()` menambahkan `Cluster` ke **copy** FE. Prediksi harus sama dengan `labels_` model asli dan distribusi audit: C0=4.820, C1=60, C2=559, C3=286. Tidak ada `fit()`, `fit_transform()`, atau `fit_predict()` di pipeline ini.

`cluster_summary.csv` memuat `Cluster`, `Record_Count`, `Record_Percentage`, `Unique_NIM_Count`, serta kolom `Mean_<fitur>` untuk delapan input dan empat LO. NIM dapat muncul dalam lebih dari satu cluster melalui record berbeda; jumlah NIM unik tiap cluster tidak boleh dijumlahkan sebagai total mahasiswa unik.

File turunan ditulis melalui staging file dan penggantian per file; manifest ditulis terakhir. Loader menolak batch yang tidak lengkap atau hash-nya tidak cocok. Mekanisme ini tidak menjanjikan transaksi multi-file atomik jika proses/mesin berhenti saat penulisan. File CSV menggunakan UTF-8 BOM untuk pembacaan Excel; import identifier sebagai teks saat membuka CSV di Excel.

`reporting_manifest.json` mencatat waktu UTC pembuatan, urutan fitur, versi paket, metadata model, hash sumber dan output, serta keterbatasan audit. Artefak adalah hasil prediksi atas FE audit, bukan hasil rekonstruksi raw → FE atau retraining. Data turunan masih memuat identifier mahasiswa; anonimisasi ekspor publik belum dikerjakan.

**Keterbatasan yang masih terbuka**

- Mismatch `Ketepatan_pct` terhadap kandidat rumus raw timestamp/deadline pada 1.886 baris belum diselesaikan. Nilai FE dipakai sesuai model terverifikasi dan keterbatasan dicatat pada manifest/app. Mismatch kontrak baru tetap menyebabkan error; temuan audit lama ini tidak dihitung ulang sebagai FE baru.
- Rumus/provenance asli `Course_pct`, `Dosen_pct`, dan `Ketepatan_pct` belum tersedia pada notebook clustering.
- IQR `Submit_pct` nol dan distribusi cluster tidak seimbang; interpretasi memerlukan konteks ini.
- Persona cluster final, validasi akademik narasi, UMAP/t-SNE, anonimisasi penuh untuk publik, dan inference data baru belum dibuat. MVP memakai label sementara dan PCA untuk proyeksi 2D.
- Tidak ada perubahan/retraining model, rerun notebook, atau deployment hosting pada tahap ini.

Pada pemeriksaan sebelum implementasi UI, folder `data/processed/` ditemukan kosong. Artefak reporting dibuat kembali melalui pipeline tervalidasi; lima file sumber tetap identik dengan hash audit. Temuan Ketepatan_pct tetap terbuka dan tidak diperbaiki dengan mengubah data asli.

`requirements.txt` memuat dependency runtime MVP. Paket untuk menjalankan seluruh notebook (matplotlib, seaborn, statsmodels, IPython/ipykernel, dan UMAP opsional) didokumentasikan di audit dan belum ditambahkan sebagai kebutuhan runtime app.

**Mengatasi Permission denied pada reporting di Windows**

Manifest/CSV dapat valid secara isi tetapi tidak dapat dibaca oleh akun desktop jika izin Windows hanya diberikan pada akun pembuat file. Bug export terdahulu menggunakan `TemporaryDirectory` yang pada Python 3.13 Windows memiliki ACL khusus pemilik. Saat file dipindahkan ke `data/processed/`, ACL khusus tersebut ikut terbawa. Export sekarang memakai staging directory biasa yang mewarisi izin folder output, sehingga file hasilnya mengikuti izin folder proyek.

Izin ketiga artefak reporting yang sudah ada dipulihkan ke izin turunan folder `data/processed/`. Isi file dan hash tidak berubah. Jika salinan lama masih mengalami masalah yang sama, jalankan dari folder proyek:

```powershell
icacls '.\data\processed\reporting_manifest.json' /reset
icacls '.\data\processed\clustered_data.csv' /reset
icacls '.\data\processed\cluster_summary.csv' /reset
```

Perintah tersebut hanya memulihkan ACL tiga file turunan ke izin folder induknya; tidak memberikan akses baru untuk seluruh proyek dan tidak mengubah isi file. Jika Windows menolak perubahan ACL, minta pemilik folder memulihkan izin baca untuk akun yang menjalankan Streamlit. Loader melaporkan kegagalan izin baca sebagai masalah akses, terpisah dari JSON/schema yang tidak valid.

Pesan `Catatan audit kualitas data: Ketepatan_pct ...` menjelaskan temuan audit yang masih terbuka. Catatan tersebut tidak menghentikan reporting; error akses file adalah masalah operasional yang berbeda. Setelah izin file dipulihkan, refresh halaman Streamlit atau hentikan server dengan Ctrl+C lalu jalankan kembali perintah startup di atas.
