# House Price: DVC, MLflow, dan GitHub Actions

Proyek California Housing dengan kode di `src/house_price`, notebook sebagai panduan belajar, dan Docker image untuk menjalankan training atau prediksi melalui CLI. Scaler dan Random Forest disimpan sebagai satu pipeline. Model menerima delapan fitur mentah; jangan lakukan scaling lagi sebelum prediksi.

Repository: [bayuzen19/mlops_house_price](https://github.com/bayuzen19/mlops_house_price).

Untuk kelas, mulai dari [Panduan Mengajar](docs/PANDUAN_MENGAJAR.md) dan [Lembar Latihan Peserta](docs/LATIHAN_PESERTA.md). Notebook memakai `configs/quick.yaml`; grid lengkap tetap tersedia di `params.yaml`.

Versi cetak: [Panduan PDF](output/pdf/Panduan_Mengajar_MLOps_House_Price.pdf) dan [Lembar Latihan PDF](output/pdf/Lembar_Latihan_MLOps_House_Price.pdf). Untuk memperbarui PDF setelah mengedit Markdown, instal extra `docs` dengan `python -m pip install -e ".[docs]"`, lalu jalankan `python scripts/export_guides.py`.

## Pilih notebook sesuai tujuan belajar

- [experiments_all_in_one.ipynb](notebooks/experiments_all_in_one.ipynb): mulai dari awal, seluruh kode ada di notebook; 23 tahap dari setup, Git/DVC, training, MLflow, hingga load model dan prediksi. Tidak mengimpor modul `house_price`.
- [experiments.ipynb](notebooks/experiments.ipynb): memakai modul `src/house_price` untuk memperlihatkan struktur proyek yang dapat dites dan dijalankan melalui CLI.

Untuk belajar dari nol, buka notebook **all-in-one**, pilih kernel Python 3.13 dari `.venv`, lalu jalankan cell berurutan. Mode cepat aktif secara default. File notebook yang lama tetap tersedia.

Paket ZIP untuk peserta berisi kode dan konfigurasi tanpa dokumentasi PDF, environment, cache, dataset, atau model. Baca `MULAI_DARI_ZIP.md` setelah ekstraksi; dataset publik disiapkan dengan pemeriksaan checksum. Buat ulang ZIP dengan `python scripts/package_project.py`.

## Server MLflow untuk kedua notebook

Jalankan di terminal PowerShell terpisah dari root proyek **sebelum Run All**:

```powershell
New-Item -ItemType Directory -Force .mlflow/server
.\.venv\Scripts\python.exe -m mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri sqlite:///.mlflow/server/mlflow.db --artifacts-destination .mlflow/server/artifacts --serve-artifacts
```

Buka [MLflow lokal](http://127.0.0.1:5000), lalu biarkan terminal server berjalan. Kedua notebook mengirim run dan model ke alamat tersebut. Untuk CLI tambahkan `--tracking-uri http://127.0.0.1:5000` pada perintah training. Default CLI tanpa argumen tetap menyediakan SQLite lokal untuk mode offline. Server menyimpan riwayat di `.mlflow/server`, terpisah dari database lokal lama.

## Struktur

```text
src/house_price/
  config.py       Parameter training dari params.yaml
  data.py         Persiapan, validasi, dan checksum dataset
  versioning.py   Perintah DVC
  train.py        Pipeline, GridSearchCV, evaluasi, dan MLflow
  predict.py      Load model dan prediksi
  cli.py          Perintah prepare-data, train, predict
notebooks/experiments.ipynb
notebooks/experiments_all_in_one.ipynb
tests/            Pengujian data, DVC, training, dan CLI
scripts/          Validasi notebook dan pengujian container
params.yaml       Konfigurasi training
dvc.yaml          Pipeline training yang dapat dijalankan ulang
Dockerfile
.github/workflows/ci-cd.yml
```

## Instalasi lokal

Gunakan **Python 3.13**. Di terminal PowerShell pada folder proyek:

```powershell
Set-Location 'F:\programming\mylearning\machine learning\house_price'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m house_price --help
```

Lewati pembuatan `.venv` jika environment sudah ada. `pyproject.toml` menjadi sumber dependency; TensorFlow, Keras, dan Hyperopt tidak diperlukan oleh alur Random Forest ini. Paket yang sebelumnya sudah terpasang tidak dihapus.

## Dataset dan DVC

Folder kerja ini sudah memiliki Git, DVC, dan CSV. Pada proyek yang benar-benar baru, jalankan `git init` dan `python -m dvc init` terlebih dahulu.

```powershell
.\.venv\Scripts\python.exe -m house_price prepare-data
.\.venv\Scripts\python.exe -m dvc add data/raw/california_housing.csv
.\.venv\Scripts\python.exe -m dvc status data/raw/california_housing.csv.dvc
```

`prepare-data` tidak menimpa CSV yang ada. Setelah clone, jika metadata `.dvc` tersedia tetapi CSV tidak ada, pulihkan dengan `dvc pull` dari remote yang sudah dikonfigurasi, atau `dvc checkout` jika cache tersedia. Cache/remote dataset tidak dimasukkan ke Docker image. Konfigurasi remote belum diisi; salin data/cache yang sesuai atau siapkan remote sebelum training dari clone baru.

Untuk dataset awal publik pada clone baru, tersedia bootstrap yang memeriksa kecocokan checksum sebelum menulis file:

```powershell
.\.venv\Scripts\python.exe -m house_price prepare-data --from-source
.\.venv\Scripts\python.exe -m dvc add data/raw/california_housing.csv
```

Jika versi DVC sudah berisi dataset modifikasi, bootstrap akan menolak data sumber yang berbeda; pulihkan versi tersebut dari cache/remote.

Simpan metadata dan kode ke Git; jangan commit CSV, cache DVC, `.venv`, atau data MLflow. Setelah perubahan data: `dvc add`, lalu commit file `.dvc`. Untuk kembali ke versi tertentu: `git restore --source=<commit> -- data/raw/california_housing.csv.dvc`, lalu `dvc checkout data/raw/california_housing.csv.dvc`. Simpan perubahan yang ingin dipertahankan sebelum restore.

## Training

Jalankan langsung tanpa server MLflow:

```powershell
.\.venv\Scripts\python.exe -m house_price train --config params.yaml
```

Tracking default disimpan di `.mlflow/mlflow.db`, beserta artifacts di `.mlflow/artifacts`. Output portabel ada di `artifacts/training/model`, sedangkan metrik dan URI model ada di `metrics.json` dan `run.json`. Pilih `--output artifacts/run-02` untuk run berikutnya agar hasil sebelumnya tidak tertimpa. Grid lengkap mengikuti notebook sebelumnya: 24 kombinasi, masing-masing 3 fold.

Untuk demo kelas, gunakan `--config configs/quick.yaml`: dua kandidat dan dua fold, memakai dataset penuh.

Untuk server MLflow yang sudah berjalan:

```powershell
.\.venv\Scripts\python.exe -m house_price train --tracking-uri http://127.0.0.1:5000 --output artifacts/server-run-01
```

Atau gunakan environment variable `MLFLOW_TRACKING_URI`. CLI mengutamakan `--tracking-uri`. Setiap run mencatat hash dataset, metadata DVC, parameter, metrik, serta model lengkap. CSV harus cocok dengan metadata DVC; perubahan yang belum dicatat akan ditolak sebelum training.

Untuk pipeline DVC, gunakan dari awal sebagai alternatif CLI langsung:

```powershell
$env:PATH = "$PWD\.venv\Scripts;$env:PATH"
.\.venv\Scripts\python.exe -m dvc repro
```

DVC mengelola output `artifacts/training` saat menjalankan ulang stage. Simpan hasil CLI langsung di folder lain bila ingin mempertahankannya sebelum mulai memakai `dvc repro`. Commit `dvc.lock` setelah pipeline berhasil. Cache DVC menyimpan model portabel, sedangkan riwayat run tetap berada di penyimpanan MLflow.

## Prediksi

CSV input harus memiliki `MedInc`, `HouseAge`, `AveRooms`, `AveBedrms`, `Population`, `AveOccup`, `Latitude`, dan `Longitude`. Urutan kolom akan disesuaikan. Target California Housing dinyatakan dalam satuan 100.000 USD.

```powershell
.\.venv\Scripts\python.exe -m house_price predict --model-uri artifacts/training/model --input data/raw/california_housing.csv --output predictions.csv
```

Untuk model dari MLflow, ganti `--model-uri` dengan URI pada `run.json` dan gunakan `--tracking-uri` dari training yang sama. File output prediksi harus belum ada.

## Notebook

Pilih kernel `.venv`, lalu jalankan `notebooks/experiments.ipynb` dari atas. Notebook memanggil modul yang sama dengan CLI, sehingga logika training tidak diduplikasi. Panduan DVC dan contoh load model tetap tersedia. Output notebook memakai folder run baru setiap kali training dijalankan.

## Pengujian lokal

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts/check_notebook.py
.\.venv\Scripts\python.exe scripts/smoke_test.py
.\.venv\Scripts\python.exe -m build
```

Tes memakai data sintetis deterministik, database MLflow sementara, dan repo DVC sementara. CI tidak mengunduh dataset California Housing atau menjalankan grid training penuh.

## Docker

Docker Desktop harus aktif dengan Linux containers:

```powershell
docker build -t house-price:local .
docker run --rm house-price:local --help
docker run --rm --network none --entrypoint python house-price:local /app/scripts/smoke_test.py
docker run --rm --mount "type=bind,source=$($PWD.Path),target=/workspace" house-price:local train --config /app/params.yaml --output artifacts/docker-run-01
docker run --rm --mount "type=bind,source=$($PWD.Path),target=/workspace" house-price:local predict --model-uri artifacts/docker-run-01/model --input data/raw/california_housing.csv --output predictions-docker.csv
```

Image berisi aplikasi, bukan dataset atau model hasil training. Mount menyediakan CSV, metadata DVC, dan lokasi output persisten. Untuk Linux, pastikan folder mount bisa ditulis UID 10001 atau jalankan dengan `--user "$(id -u):$(id -g)"`. Gunakan path model portabel untuk pertukaran host/container; URI artifact lokal MLflow bisa mengandung path khusus host. Untuk server MLflow di host Windows, gunakan `http://host.docker.internal:5000` dari container jika server dikonfigurasi untuk menerima koneksi tersebut.

## CI/CD ke GitHub Container Registry

Workflow `.github/workflows/ci-cd.yml` menjalankan:

1. **CI:** lint, format, tes di Ubuntu dan Windows, validasi notebook, dan build paket Python.
2. **Container:** build image dan uji training/load/prediksi tanpa jaringan.
3. **CD:** setelah seluruh pemeriksaan lolos, build kandidat rilis, uji kandidat itu, lalu push image yang sama ke GHCR tanpa rebuild.

Pull request hanya menjalankan pemeriksaan. Push ke `main`/`master` atau tag `v*` menjalankan publikasi. Pemicu manual dapat mempublikasikan dari `main`/`master`. Image bernama `ghcr.io/<owner>/<repository>` dengan tag SHA commit, branch/tag Git, dan `latest` hanya untuk default branch. Tag `v*` sebaiknya diproteksi melalui aturan repository.

Publikasi memakai `GITHUB_TOKEN` bawaan dengan `packages: write` hanya pada job publish, sesuai [panduan GitHub untuk Docker images](https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images). Tidak perlu menyimpan PAT untuk workflow ini. Pengaturan organisasi harus mengizinkan Actions menulis packages; jika package sudah dibuat sebelumnya, berikan repository ini akses ke package tersebut. Package baru dapat bersifat private sesuai pengaturan akun.

Remote proyek adalah `https://github.com/bayuzen19/mlops_house_price.git`. Peserta kelas sebaiknya memakai fork masing-masing. Commit dan push kode ke `main` atau `master` untuk memicu workflow publikasi. Jangan menjalankan `git add .` tanpa meninjau file. Contoh daftar file yang perlu masuk:

```powershell
git add src tests scripts notebooks configs docs .github Dockerfile .dockerignore .gitattributes pyproject.toml requirements.txt requirements-dev.txt params.yaml dvc.yaml .dvc .dvcignore .gitignore data/raw/.gitignore data/raw/california_housing.csv.dvc README.md
git diff --cached --stat
git commit -m "Structure ML project and add GHCR CI/CD"
```

Periksa tab **Actions** dan halaman **Packages** untuk bukti hasil publikasi. Label workflow hijau menunjukkan hasil commit tersebut; keberadaan Dockerfile saja belum membuktikan image berhasil dipublikasikan.
