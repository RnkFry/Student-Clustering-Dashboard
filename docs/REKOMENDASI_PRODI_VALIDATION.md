# Validasi sumber Rekomendasi Strategis Prodi

Inspeksi dilakukan pada 9 November 2026 sebelum implementasi, menggunakan pandas dan openpyxl dalam environment proyek. Dokumen rencana yang tersedia adalah `PROJECT_PLAN_DASHBOARD_STREAMLIT_BINUS_REVISED.md`; `PROJECT_PLAN.md` tidak tersedia. Panduan yang dibaca: AGENTS.md, rencana tersebut, FEATURE_REKOMENDASI_PRODI.md, dan README.md.

## Workbook

- Sumber: `data/reference/Rekomendasi Prodi.xlsx`.
- Sheet: `Sheet1` (satu sheet).
- Dimensi worksheet: 13 baris × 4 kolom; kolom A kosong.
- Pembacaan default header=0 menghasilkan 12 baris dan kolom `Unnamed: 0` sampai `Unnamed: 3` karena baris awal kosong/judul.
- Header aktual: B9:D9; data mapping: B10:D13, empat baris × tiga kolom.
- Kolom aktual: `Cluster dan nama profil`, `Karakteristik empiris`, `Rekomendasi strategis untuk pengelola Prodi pada semester berikutnya`.
- Normalisasi hanya memisahkan nomor cluster dan nama profil. Teks karakteristik/rekomendasi, tanda baca, spasi, serta baris baru dipertahankan dari Excel.
- Tidak ditemukan duplicate, missing, unknown ID, atau identitas profil yang tertukar.

| ID | Nama profil sesuai Excel | Baris Excel | Record | NIM unik |
| --- | --- | --- | ---: | ---: |
| 0 | High Achievement and Consistent Engagement | 10 | 4.820 | 536 |
| 1 | Critical Engagement and Assessment Support | 11 | 60 | 37 |
| 2 | Developing Learning Engagement and LO Attainment | 12 | 559 | 231 |
| 3 | Learning Engagement and Achievement Improvement | 13 | 286 | 115 |

## Kecocokan model dan reporting

Model tersimpan adalah KMeans dengan `n_features_in_=8`, `n_clusters=4`; scaler tersimpan adalah RobustScaler dengan delapan fitur. Semua 5.725 label pada `clustered_data.csv` sama persis dengan `model.labels_` pada urutan record tersimpan. Hash lima sumber model/data/notebook cocok dengan kontrak audit existing. Tidak ada retraining atau relabeling.

Urutan input tetap: Course_pct, Dosen_pct, FD_pct, PPT_pct, LN_pct, VBL_pct, Submit_pct, Ketepatan_pct. Empat LO tersedia pada reporting sebagai avg_LO1, avg_LO2, avg_LO3, Total_LO dan tidak termasuk input model.

Rata-rata aktual global, dibulatkan tiga desimal:

| Cluster | FD_pct | VBL_pct | Submit_pct | Ketepatan_pct | avg_LO1 | avg_LO2 | avg_LO3 | Total_LO |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 69.876 | 69.944 | 100.000 | 93.074 | 30.771 | 37.931 | 17.868 | 86.571 |
| 1 | 29.000 | 29.333 | 18.611 | 15.278 | 6.924 | 5.498 | 2.656 | 15.078 |
| 2 | 50.644 | 51.771 | 83.333 | 76.148 | 24.424 | 31.039 | 15.246 | 70.709 |
| 3 | 42.133 | 41.748 | 63.578 | 54.254 | 14.195 | 21.166 | 9.912 | 45.272 |

Profil LO cocok dengan referensi eksperimen pada spesifikasi hingga tiga desimal. Pola relatif pada Total_LO, FD_pct, VBL_pct, Submit_pct, dan Ketepatan_pct mendukung karakteristik empiris Excel. Angka dalam dokumen ini adalah hasil inspeksi, bukan konstanta yang digunakan service atau UI. Tidak ditambahkan threshold tinggi/rendah atau klaim kausal baru.

## Integrasi dan batasan

`app.py` tetap menjadi router tunggal; section baru memakai `render()`. `reporting_view()` menyediakan data global dan subset filter yang memuat label tersimpan. Service hanya memilih record berdasarkan ID dan menghitung rata-rata. Workbook dibaca oleh loader terpisah dengan cache berbasis isi; UI tidak memanggil model, scaler, atau prediksi.

Nama profil Excel diperiksa terhadap kontrak spesifikasi agar pertukaran ID/nama tidak diterima diam-diam. Keabsahan substansi teks yang kelak diubah pengelola tetap membutuhkan review; schema validation bukan validasi akademik otomatis.

Keterbatasan audit existing tetap berlaku: provenance Ketepatan_pct belum tuntas pada 1.886 baris; Submit_pct memiliki IQR nol; ukuran cluster tidak seimbang. Satu NIM dapat muncul pada beberapa cluster melalui record mata kuliah yang berbeda. Istilah relatif dalam Excel mengacu pada profil global, bukan threshold absolut atau kesimpulan otomatis untuk setiap subset.

Loader reporting existing tetap ketat pada schema dan hash. Jika file reporting kehilangan fitur/LO atau diubah, aplikasi menampilkan kegagalan validasi sumber, bukan memperbaikinya diam-diam. Service dan presentation layer juga menyediakan status data tidak tersedia untuk input parsial tanpa membuat angka pengganti.

## Hasil pengujian

`python -B -m unittest discover -s tests -v` pada environment proyek: **36 tests lulus** (13 tests rekomendasi baru dan 23 regresi existing), tanpa skip, dalam sekitar 10 detik. Cakupan termasuk sembilan menu melalui Streamlit AppTest, empat pilihan cluster, schema chart, filter/empty/error state, ketepatan teks Excel, invalidasi cache, validasi mapping, profil eksternal LO, serta integritas hash sumber dan reporting. `git diff --check` tidak menemukan masalah whitespace.

Tidak dilakukan review visual piksel pada browser, deployment, retraining, atau perubahan dependency. Python default pada mesin belum memiliki openpyxl; environment `Binus-Project-Venv` yang tercantum pada README sudah memiliki dependency yang diperlukan.
