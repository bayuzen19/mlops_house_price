# Lembar Latihan Peserta — House Price MLOps

Nama: ____________________  Repository/fork: ____________________

Gunakan [Panduan Mengajar](PANDUAN_MENGAJAR.md) sebagai petunjuk perintah. Semua latihan perubahan kode/Git dilakukan pada fork atau branch latihan milik sendiri.

## Persiapan - Jalankan notebook lengkap dan server

Gunakan `notebooks/experiments_all_in_one.ipynb` untuk praktik dari awal. Notebook modular tetap tersedia sebagai tahap berikutnya. Pilih kernel Python 3.13 dari `.venv` proyek. Di terminal terpisah dari root proyek, jalankan:

```powershell
New-Item -ItemType Directory -Force .mlflow/server
.\.venv\Scripts\python.exe -m mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri sqlite:///.mlflow/server/mlflow.db --artifacts-destination .mlflow/server/artifacts --serve-artifacts
```

Buka http://127.0.0.1:5000 dan biarkan terminal server berjalan. Jalankan notebook per tahap, lalu catat bukti berikut. Nomor tahap mengacu pada judul Markdown notebook.

| Tahap | Tindakan peserta | Bukti yang dicatat |
|---|---|---|
| 01-05 | Periksa kernel, import, path, Git/DVC | Python aktif, root proyek, versi DVC |
| 06-09 | Siapkan CSV, dvc add, baca, validasi | Shape, SHA-256, isi file .dvc |
| 10-12 | Split, pipeline, grid | Ukuran train/test dan jumlah kandidat/fitting |
| 13-14 | Fit dan evaluasi | Best params, CV MSE, test MSE, baseline MSE |
| 15-17 | Log ke HTTP5000 dan ekspor | Experiment, run ID, model URI, path run.json |
| 18-20 | Load dari server dan folder | Pesan PASS serta CSV contoh prediksi |
| 21-23 | Buka UI dan telusuri metadata | Hubungan run, data, model, dan kode |

Setelah selesai, restart kernel dan jalankan ulang untuk memastikan urutan notebook lengkap. Jangan menutup server sebelum logging/loading selesai. Gunakan mode cepat; waktu training tidak menjadi kriteria kelulusan karena bergantung komputer.

**Tugas penjelasan:** pilih masing-masing satu baris kode dari validasi, split, pipeline, logging, dan loading. Jelaskan input, hasil, dan akibat bila baris tersebut dihapus. Jawaban harus mengacu pada variabel yang benar dalam notebook.

**Tugas pemulihan:** catat path `run.json`, restart kernel, import json, Path, dan mlflow, isi path laporan tersebut, lalu load model tanpa training ulang. Gunakan lima baris fitur mentah dari CSV sebagai input. Bukti: model URI yang sama dan prediksi berhasil.

## Latihan 1 — Petakan proyek

Jalankan CLI `--help`, lalu jelaskan dengan kalimat sendiri:

| Pertanyaan | Jawaban |
|---|---|
| Di mana parameter model disimpan? | |
| Modul mana yang memeriksa versi dataset? | |
| Modul mana yang menyimpan model ke MLflow? | |
| Mengapa notebook memanggil modul Python? | |

**Bukti:** keluaran `--help` dan Python yang digunakan oleh kernel.

## Latihan 2 — Dua versi dataset

1. Siapkan dataset awal dan catat ukuran serta SHA-256.
2. Pastikan dataset berada di cache DVC dan tandai commit baseline.
3. Buat varian 80% baris dengan seed 42.
4. Amati `dvc status` sebelum dan sesudah `dvc add`.
5. Commit metadata versi baru.
6. Restore baseline dan buktikan hash kembali sama.

| Versi | Jumlah baris | SHA-256 | Commit/tag |
|---|---:|---|---|
| Baseline | | | |
| Varian 80% | | | |
| Setelah restore | | | |

**Pertanyaan:** apakah file `.dvc` sendiri cukup untuk memulihkan CSV pada komputer baru? Jelaskan peran cache/remote.

## Latihan 3 — Catat eksperimen

Jalankan training CLI dengan `configs/quick.yaml` dan `--tracking-uri http://127.0.0.1:5000` agar run tercatat pada server kelas yang sama. Pilih folder output baru untuk tiap eksperimen. Buka MLflow UI dan lengkapi:

| Item | Nilai |
|---|---|
| Run ID | |
| Experiment | |
| Dataset SHA-256 | |
| Parameter terbaik | |
| CV MSE | |
| Test MSE | |
| Test R² | |
| Model URI | |

**Pertanyaan:** jika CV MSE dan test MSE berbeda, apakah itu otomatis menunjukkan bug? Mengapa?

## Latihan 4 — Gunakan kembali model

1. Prediksi menggunakan folder model portabel.
2. Prediksi menggunakan URI model MLflow dari run yang sama.
3. Bandingkan hasil keduanya.
4. Coba input yang kehilangan satu fitur dan catat pesan error.

**Bukti:** dua CSV prediksi dan hasil perbandingan. Jangan memasukkan data pribadi ke repository.

**Pertanyaan:** mengapa kita tidak melakukan `fit_transform()` ulang pada data prediksi?

## Latihan 5 — Jalankan quality checks

Jalankan lint, format check, pytest, dan validasi notebook. Pada branch latihan, tambahkan satu unused import, amati pemeriksaan yang gagal, lalu perbaiki.

| Pemeriksaan | Hasil awal | Setelah perbaikan |
|---|---|---|
| Ruff check | | |
| Ruff format | | |
| Pytest | | |
| Notebook validation | | |

**Pertanyaan:** apakah semua tes lolos berarti model sudah layak untuk semua penggunaan bisnis?

## Latihan 6 — Pipeline DVC

1. Gunakan konfigurasi quick sebagai parameter stage latihan.
2. Jalankan `dvc repro` dua kali tanpa mengubah input.
3. Catat apakah run kedua melakukan training.
4. Ubah satu parameter, lalu jalankan kembali.
5. Periksa perubahan `dvc.lock` dan laporan run.

**Bukti:** log run pertama, run kedua, dan run setelah perubahan parameter.

## Latihan 7 — Container dan GHCR

1. Build Docker image dan jalankan smoke test.
2. Buat pull request pada fork sendiri.
3. Periksa job `quality` dan `container`.
4. Setelah CI lolos, pemilik fork merge ke branch utama.
5. Periksa job `publish` dan package GHCR.
6. Pull tag image yang dihasilkan dan jalankan `--help`.

| Item | Bukti/URL |
|---|---|
| Pull request | |
| Workflow run | |
| Commit SHA | |
| GHCR package/tag | |
| Hasil `docker run --help` | |

Jika Docker lokal belum dapat berjalan, jelaskan penyebabnya dan bedakan bukti dari GitHub runner dengan bukti eksekusi lokal.

## Refleksi

Tuliskan alur satu eksperimen dari dataset sampai image dalam 5–8 kalimat. Sertakan cara menemukan versi data, konfigurasi training, model, serta commit image. Sebutkan satu bagian yang masih memerlukan pekerjaan tambahan sebelum aplikasi dijalankan sebagai layanan produksi.

## Kunci diskusi ringkas untuk pengajar

- Kernel menentukan Python yang mengeksekusi cell. Library yang diinstal ke Python lain belum tentu dapat diimpor kernel.
- Server HTTP menerima catatan dan artifact; UI berada pada http://127.0.0.1:5000. Database lokal server menyimpan metadata, sedangkan folder artifact menyimpan file model.
- Tahap load tidak membutuhkan fit ulang. Laporan run menyimpan identitas model, tetapi tidak menggantikan keberadaan artifact model dan akses ke tracking store.
- Best estimator merupakan pemenang CV pada grid dan data tertentu. Nama registered model tidak otomatis berarti model terbaik untuk semua kebutuhan bisnis.

- `.dvc` berisi rujukan dan hash; isi data tetap memerlukan cache atau remote.
- CV dan test memakai pembagian data berbeda. Perbedaan skor perlu dianalisis, bukan otomatis dianggap bug.
- Scaler inference memakai statistik training agar transformasi konsisten; pipeline menyimpan keduanya.
- Tes memeriksa perilaku yang dirancang, sementara kelayakan bisnis memerlukan evaluasi kualitas dan kondisi penggunaan.
- `dvc repro` menggunakan perubahan dependency/parameter untuk menentukan apakah stage perlu dijalankan ulang.
- GHCR menyimpan image. Untuk layanan produksi masih diperlukan runtime deployment, akses data/model, monitoring, dan prosedur pembaruan sesuai kebutuhan.
