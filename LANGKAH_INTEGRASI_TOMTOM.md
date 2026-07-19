# Langkah-Langkah Integrasi TomTom (Live Traffic)

Dokumen ini berisi panduan dan rencana teknis untuk mengganti sistem OSRM saat ini menjadi TomTom Routing API, guna mendapatkan data kemacetan lalu lintas secara *real-time* di aplikasi Optimasi Rute.

## 1. Persiapan Akun & API Key TomTom
Anda perlu mendapatkan API Key gratis dari portal khusus Developer TomTom, bukan portal Analytics (Move).
1. Buka situs [TomTom Developer Portal](https://developer.tomtom.com/).
2. Klik tombol **"Get your free API key"** atau **"Register"** di pojok kanan atas.
3. Buat akun menggunakan email Anda.
4. Setelah login, masuk ke menu **Dashboard** -> **Keys**.
5. Di sana akan ada *My First API Key* (atau Anda bisa klik "Add a new key").
6. Salin API Key tersebut. Nantinya kita akan memasukkannya ke dalam file `.env`.

## 2. Rencana Modifikasi Backend (Python)
Ketika Anda sudah memiliki API Key TomTom, saya (*AI*) akan melakukan perubahan berikut:

### A. Konfigurasi Environment
- Menginstal library `python-dotenv` untuk membaca file `.env`.
- Menambahkan `TOMTOM_API_KEY` ke `settings.py`.

### B. Membuat `tomtom_client.py` (Pengganti OSRM)
Saya akan membuat *class* baru di folder `routing/ai_core/` untuk komunikasi dengan TomTom API:
- **`get_distance_matrix_traffic()`**: Menggunakan [TomTom Routing Matrix API](https://developer.tomtom.com/routing-api/documentation/matrix-routing-v2/matrix-routing) dengan parameter `computeTravelTimeFor=all` dan menyertakan `traffic=true`. Ini akan mengembalikan matriks **waktu tempuh aktual** di kondisi lalu lintas saat ini.
- **`get_route_geometry_traffic()`**: Menggunakan [TomTom Calculate Route API](https://developer.tomtom.com/routing-api/documentation/routing/calculate-route) dengan parameter lalu lintas aktif.

### C. Menyesuaikan `aco_optimizer.py`
Saat ini, algoritma ACO Anda meminimalkan "Jarak (km)". Saya akan mengubah target optimasi (Fitness Function) menjadi meminimalkan **"Waktu Tempuh / Durasi (detik/menit)"** karena rute terpendek belum tentu tercepat jika macet.

### D. Mengubah `views.py`
- Menghubungkan perhitungan ACO dengan `TomTomClient`.
- Menyesuaikan halaman `result.html` agar menampilkan penghematan waktu (durasi) perjalanan akibat kemacetan.

---

**Status:** *Menunggu API Key dari Pengguna.*
Jika Anda sudah mendapatkan API Key dari *developer.tomtom.com*, berikan kodenya di obrolan ini dan katakan: *"Saya sudah punya TomTom API Key, mari mulai eksekusi!"*.
