# Estiga-Project

Sistem web sederhana untuk melakukan estimasi nilai pinjaman berdasarkan barang yang akan digadaikan.

## Fitur

- Form input data barang gadai
- Perhitungan otomatis estimasi pinjaman
- Riwayat estimasi
- Interface yang responsif dan mudah digunakan

## Teknologi yang Digunakan

- Python Flask
- MySQL
- Bootstrap 5
- HTML/CSS

## Instalasi

1. Clone repository ini
2. Buat virtual environment Python:
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. Install dependensi:
   ```
   pip install -r requirements.txt
   ```
4. Buat database MySQL:
   ```
   CREATE DATABASE estimasi_gadai;
   ```
5. Sesuaikan konfigurasi database di file `.env`
6. Jalankan aplikasi:
   ```
   python app.py
   ```

## Struktur Proyek

```
estimasi-gadai/
├── app.py              # File utama aplikasi Flask
├── requirements.txt    # Daftar dependensi
├── .env               # Konfigurasi environment
├── static/            # File statis (CSS, JS, dll)
│   └── style.css
└── templates/         # Template HTML
    ├── base.html
    ├── index.html
    ├── estimasi.html
    ├── hasil.html
    └── riwayat.html
```

## Penggunaan

1. Buka browser dan akses `http://localhost:5000`
2. Klik "Mulai Estimasi" untuk membuat estimasi baru
3. Isi form dengan data barang yang akan digadaikan
4. Sistem akan menghitung estimasi pinjaman secara otomatis
5. Lihat riwayat estimasi di menu "Riwayat" 
