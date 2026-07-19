# Langkah-Langkah Integrasi Mapbox (Live Traffic)

Dokumen ini berisi panduan dan rencana teknis untuk mengganti sistem OSRM saat ini menjadi Mapbox Directions API, guna mendapatkan data kemacetan lalu lintas secara *real-time* di aplikasi Optimasi Rute.

## 1. Persiapan Akun & API Key Mapbox
Sebelum sistem bisa dimodifikasi, Anda perlu menyiapkan API Key:
1. Buka situs [Mapbox](https://www.mapbox.com/) dan buat akun gratis.
2. Setelah login, masuk ke **Dashboard** -> **Tokens**.
3. Buat token baru atau salin *Default Public Token* yang sudah ada (dimulai dengan `pk....`).
4. Simpan token tersebut. Nantinya kita akan memasukkannya ke dalam file konfigurasi Django (seperti `.env`).

## 2. Rencana Modifikasi Backend (Python)
Ketika Anda sudah siap mengimplementasikan Mapbox, ini adalah langkah-langkah yang akan saya (*AI*) lakukan pada kode Anda:

### A. Konfigurasi Environment
- Menginstal library `python-dotenv` (jika belum ada) untuk menyimpan API Key secara aman di file `.env`.
- Membaca variabel `MAPBOX_ACCESS_TOKEN` di `settings.py`.

### B. Membuat `mapbox_client.py` (Pengganti OSRM)
Saya akan membuat sebuah *class* baru di folder `routing/ai_core/` yang bertugas untuk berkomunikasi dengan Mapbox API. Fungsi utamanya meliputi:
- **`get_distance_matrix_traffic()`**: Mengambil *Matrix API* dari Mapbox menggunakan profil `mapbox/driving-traffic` untuk mendapatkan estimasi waktu tempuh berdasarkan kondisi lalu lintas saat ini.
- **`get_route_geometry_traffic()`**: Mengambil *Directions API* dari Mapbox menggunakan profil `mapbox/driving-traffic` untuk mendapatkan rute (garis di peta) yang menghindari kemacetan.

*Catatan: Mapbox Directions API memiliki batas 25 koordinat per request (berbeda dengan OSRM yang bisa lebih dari 100). Jika titik paket Anda > 25, saya akan membuat logika pemecahan (chunking) agar rute tetap bisa dihitung secara akurat.*

### C. Menyesuaikan `aco_optimizer.py`
Saat ini, algoritma ACO Anda mengoptimalkan "Jarak (Distance)". Dengan adanya kemacetan lalu lintas, yang lebih penting adalah mengoptimalkan "Waktu Tempuh (Travel Time/Duration)" karena rute yang lebih jauh bisa jadi lebih cepat jika jalan tersebut lancar.
- Mengubah parameter ACO untuk membaca matriks *duration* alih-alih *distance*.

### D. Mengubah `views.py`
- Pada fungsi `run_optimization()`, saya akan mengganti pemanggilan `OSRMClient` menjadi `MapboxClient`.
- Menggunakan hasil perhitungan waktu tempuh yang disesuaikan dengan macet (*traffic*) sebagai acuan evaluasi rute terbaik.

## 3. Rencana Modifikasi Frontend (Peta & Tampilan)
- Karena OSRM diganti dengan Mapbox, pada file `views.py` (fungsi `generate_route_map`), kita tetap bisa menggunakan `Folium` untuk menampilkan peta.
- Garis rute (*Polyline*) yang digambar akan mengikuti geometri jalan yang bebas macet sesuai arahan Mapbox Directions.
- Saya akan memperbarui metrik di UI (Dashboard dan Hasil) agar menampilkan penghematan berdasarkan **Estimasi Waktu Tempuh** dan bukan hanya sekadar "Jarak (km)".

---

**Status:** *Menunggu API Key dari Pengguna.*
Jika Anda sewaktu-waktu sudah siap dan telah memiliki API Key Mapbox, Anda tinggal memberikan API Key tersebut di obrolan baru atau obrolan ini, lalu katakan: *"Saya sudah punya Mapbox API Key, mari eksekusi sesuai file LANGKAH_INTEGRASI_MAPBOX.md"*.
