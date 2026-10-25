# Mulai dari paket ZIP House Price

Ekstrak ZIP sampai folder `house_price` terlihat, lalu buka folder tersebut di VS Code. Buka terminal PowerShell **di dalam folder `house_price`**, bukan di folder `notebooks`. Python 3.13 dan Git harus sudah terpasang.

## 1. Buat environment

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip check
git init
```

Folder `.dvc` sudah disertakan; tidak perlu `dvc init` lagi. ZIP tidak memiliki riwayat `.git`, sehingga `git init` membuat repository lokal baru. Bila ingin riwayat asli, gunakan `git clone https://github.com/bayuzen19/mlops_house_price.git` sebagai pengganti ZIP.

## 2. Jalankan server MLflow

Kedua notebook memakai `http://127.0.0.1:5000`. Buka terminal PowerShell kedua di root proyek sebelum menjalankan training:

```powershell
New-Item -ItemType Directory -Force .mlflow/server
.\.venv\Scripts\python.exe -m mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri sqlite:///.mlflow/server/mlflow.db --artifacts-destination .mlflow/server/artifacts --serve-artifacts
```

Buka `http://127.0.0.1:5000`. Biarkan terminal server berjalan selama logging dan load model. Hentikan dengan Ctrl+C setelah selesai. Gunakan folder dan perintah yang sama saat menyalakan server kembali agar riwayat tetap tersedia.

## 3. Pilih cara belajar

**Dari awal melalui notebook:** buka `notebooks/experiments_all_in_one.ipynb`, pilih kernel `.venv`, lalu jalankan cell dari atas ke bawah. Notebook memuat seluruh implementasi: data, DVC, pipeline, pencarian parameter, evaluasi, logging MLflow, export, dan load model. Dataset diunduh bila belum tersedia. Koneksi internet diperlukan untuk instalasi dan unduhan pertama.

**Melalui modul/CLI:** jalankan perintah berikut di terminal yang sama.

```powershell
.\.venv\Scripts\python.exe -m house_price prepare-data --from-source
.\.venv\Scripts\python.exe -m dvc add data/raw/california_housing.csv
.\.venv\Scripts\python.exe -m house_price train --config configs/quick.yaml --tracking-uri http://127.0.0.1:5000
.\.venv\Scripts\python.exe -m pytest -q
```

Training menampilkan lokasi model dan laporan run. Bila direktori output training sudah berisi hasil, gunakan lokasi output baru sesuai `python -m house_price train --help`; jangan menghapus hasil yang masih diperlukan. `notebooks/experiments.ipynb` memperlihatkan penggunaan modul yang sama.

Run kedua notebook terlihat pada server yang sama, di experiment masing-masing. Tanpa `--tracking-uri` atau environment variable, CLI memakai SQLite lokal untuk mode offline. Riwayat database lama tidak otomatis digabungkan ke server baru.

## 4. GitHub Actions dan image

Workflow ada di `.github/workflows/ci-cd.yml`. Setelah kode dipush ke repository Anda dengan branch `main`, GitHub Actions memeriksa Python di Linux/Windows, menguji container, lalu mengirim image ke `ghcr.io/<pemilik>/<repository>`. Pull request hanya menjalankan pemeriksaan, tanpa publish. Pengiriman image memakai `GITHUB_TOKEN` milik Actions dengan izin `packages: write` pada job publish.

Mengunduh ZIP saja tidak menjalankan Actions. Gunakan fork repository pengajar atau hubungkan repository Git lokal ke repository GitHub milik Anda. Jangan mengarahkan hasil latihan peserta ke repository pengajar.

## 5. Isi yang sengaja dikeluarkan

ZIP tidak memuat `docs/`, `output/`, `.git/`, `.venv/`, cache DVC, database/artifacts MLflow, model terlatih, atau CSV. Metadata dataset `.dvc` tetap disertakan. Dataset baseline publik dapat diunduh dan diverifikasi oleh perintah setup; versi dataset modifikasi membutuhkan cache/remote DVC yang sesuai.

Panduan lengkap dan lembar latihan tersedia terpisah dari ZIP:

- [Panduan mengajar](https://github.com/bayuzen19/mlops_house_price/blob/main/docs/PANDUAN_MENGAJAR.md)
- [Panduan PDF](https://github.com/bayuzen19/mlops_house_price/blob/main/output/pdf/Panduan_Mengajar_MLOps_House_Price.pdf)
- [Latihan peserta](https://github.com/bayuzen19/mlops_house_price/blob/main/docs/LATIHAN_PESERTA.md)

Jika perintah Python tidak dikenali, periksa instalasi Python 3.13 lalu buka ulang terminal. Jika dataset tidak cocok dengan metadata, pulihkan versi dari DVC; jangan mengganti checksum agar lolos. Jika Docker Desktop belum dapat menjalankan Linux containers, selesaikan notebook dan tes Python dulu; build container juga dijalankan oleh GitHub Actions.
