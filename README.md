# Sistem Optimasi Rute Dinamis - Django Version

Sistem optimasi rute pengiriman berbasis algoritma ACO (Ant Colony Optimization) dengan Django framework dan Tailwind CSS untuk wilayah Kabupaten Gresik, Jawa Timur.


## Instalasi

1. Buat virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Setup database:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. Jalankan development server:
   ```bash
   python manage.py runserver
   ```

5. Akses di browser: `http://127.0.0.1:8000`

## Struktur Proyek

```
optimasi-rute-django/
├── manage.py
├── config/           # Django settings
├── routing/          # Main app
│   ├── models.py     # Database models
│   ├── views.py      # View handlers
│   ├── forms.py      # Django forms
│   ├── templates/    # HTML templates
│   └── ai_core/      # AI algorithms
└── static/           # CSS, JS, maps
```

## Teknologi

- **Framework**: Django 5.0+
- **Frontend**: Tailwind CSS (CDN)
- **Algoritma**: MealPy ACO
- **Maps**: Folium
- **Routing**: OSRM API
- **Database**: SQLite (Django ORM)

## Kontributor

Sistem dikembangkan untuk penelitian optimasi rute pengiriman paket last-mile di Kabupaten Gresik.
# RouteOptimation_ML
