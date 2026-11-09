
# Feature Specification: Rekomendasi Strategis Prodi

## 1. Tujuan
Mengembangkan modul rekomendasi strategis berbasis hasil
clustering mahasiswa untuk mendukung evaluasi pembelajaran
oleh pengelola Program Studi BINUS.

## 2. Model ML
Model yang digunakan:
- Algorithm: K-Means
- Features: 8
- Scaler: RobustScaler
- Number of clusters: 4 (Cluster 0–3)

Fitur:
1. Course_pct
2. Dosen_pct
3. FD_pct
4. PPT_pct
5. LN_pct
6. VBL_pct
7. Submit_pct
8. Ketepatan_pct

Learning Outcome (LO1, LO2, LO3, Total_LO)
adalah profil eksternal, bukan fitur clustering.

## 3. Sumber Rekomendasi
File: data/reference/Rekomendasi Prodi.xlsx
Sheet: Sheet1

Excel merupakan sumber utama teks rekomendasi.
Baca struktur dan kolom aktual sebelum implementasi.

Jangan mengganti, mengarang, atau mengubah substansi
rekomendasi yang diberikan pengelola Prodi.

## 4. Mapping Cluster
Cluster 0: High Achievement and Consistent Engagement
Cluster 1: Critical Engagement and Assessment Support
Cluster 2: Developing Learning Engagement and LO Attainment
Cluster 3: Learning Engagement and Achievement Improvement

Validasi bahwa mapping cocok dengan hasil model final.

## 5. Referensi Profil LO

| Cluster | LO1 | LO2 | LO3 | Total_LO |
|---------|-----|-----|-----|----------|
| 0 | 30.771 | 37.931 | 17.868 | 86.571 |
| 1 | 6.924 | 5.498 | 2.656 | 15.078 |
| 2 | 24.424 | 31.039 | 15.246 | 70.709 |
| 3 | 14.195 | 21.166 | 9.912 | 45.272 |

Angka ini adalah referensi hasil eksperimen final.
Untuk dashboard, gunakan data aktual bila tersedia.
Jangan menganggap nilai referensi sebagai hasil
perhitungan dinamis.

## 6. Recommendation Logic
Gunakan rule-based mapping berdasarkan label cluster.

Input:
- Cluster ID hasil model final.
- Profil 8 fitur clustering.
- Profil LO eksternal bila tersedia.

Output:
- Cluster name.
- Karakteristik empiris.
- Rekomendasi strategis dari Excel.
- Data pendukung yang relevan.

LO bukan input untuk mengubah cluster.
Jangan membuat model rekomendasi ML tambahan.

## 7. Dashboard Requirements
Modul harus dapat:
- Menampilkan pilihan Cluster 0–3.
- Menampilkan karakteristik cluster terpilih.
- Menampilkan delapan fitur profil cluster.
- Menampilkan capaian LO eksternal.
- Menampilkan rekomendasi strategis dari Excel.
- Menampilkan data pendukung rekomendasi.
- Memberi pesan jika mapping tidak tersedia.

## 8. Engineering Requirements
- Gunakan pandas untuk Excel.
- Gunakan openpyxl sebagai Excel engine.
- Pisahkan loader, business logic, dan UI.
- Gunakan path relatif terhadap project root.
- Tidak boleh menggunakan absolute path lokal.
- Ikuti struktur Streamlit yang sudah ada.
- Tambahkan validasi mapping dan unit tests.

## 9. Acceptance Criteria
- Semua Cluster 0–3 memiliki mapping yang benar.
- Teks rekomendasi konsisten dengan Excel.
- Cluster ID tidak tertukar.
- LO tidak dimasukkan dalam prediksi K-Means.
- Tidak ada perubahan pada model ML final.
- Dashboard berjalan tanpa error.
- Tests berhasil.
