
# Project Instructions — BINUS Student Clustering Dashboard

## Project Context
- Framework dashboard: Streamlit.
- Bahasa pemrograman: Python.
- Model final: K-Means dengan 8 fitur dan RobustScaler.
- LO1, LO2, LO3, dan Total_LO adalah profil eksternal.
- Rekomendasi ditujukan kepada pengelola Prodi.

## Development Rules
1. Pertahankan model clustering dan preprocessing yang sudah final.
2. Jangan mengubah urutan fitur, model, scaler, atau label cluster.
3. Jangan melakukan retraining tanpa instruksi eksplisit.
4. Gunakan arsitektur repository yang sudah ada.
5. Gunakan clean code, modular functions, dan type hints.
6. Jangan melakukan refactoring di luar scope fitur.
7. Untuk fitur rekomendasi, baca docs/FEATURE_REKOMENDASI_PRODI.md.
8. Gunakan data/reference/Rekomendasi Prodi.xlsx sebagai sumber mapping rekomendasi.
9. Jangan membuat rekomendasi yang tidak didukung Excel atau data.
10. Tambahkan unit tests untuk logika mapping dan validasi.

## Implementation
- Gunakan pandas dan openpyxl untuk membaca Excel.
- Pisahkan data access, recommendation logic, dan UI Streamlit.
- Jelaskan perubahan file dan hasil pengujian.
