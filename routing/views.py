"""
Django Views for Route Optimization System
Request handlers untuk dashboard, optimization, dan results
Menggunakan ACO (Ant Colony Optimization) sesuai Bab III paper
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import OptimizationRun, ComparisonResult, DeliveryPoint
from .forms import DepotForm, ACOParametersForm, GenerateSampleDataForm, DeliveryPointForm
from .ai_core.aco_optimizer import ACOOptimizer
from .ai_core.baseline_nn import NearestNeighborBaseline
from .ai_core.tomtom_client import TomTomClient
from .ai_core.evaluator import RouteEvaluator
import pandas as pd
import numpy as np
import time
import json
import folium


def generate_route_map(route, delivery_points, depot_lat, depot_lon):
    """Generate Folium map for route visualization"""
    # Create map centered on depot
    m = folium.Map(
        location=[depot_lat, depot_lon],
        zoom_start=12,
        tiles='OpenStreetMap'
    )

    # Add depot marker
    folium.Marker(
        location=[depot_lat, depot_lon],
        popup='Depot (Start/End)',
        tooltip='Depot',
        icon=folium.Icon(color='red', icon='home', prefix='fa')
    ).add_to(m)

    # Add delivery point markers
    for i, node_id in enumerate(route[1:], 1):  # Skip depot (first item)
        if node_id == 0:  # Skip if returning to depot
            continue

        try:
            point = delivery_points.get(node_id=node_id)
            folium.Marker(
                location=[point.latitude, point.longitude],
                popup=f'Node {node_id}<br>Order: {i}<br>Demand: {point.demand}',
                tooltip=f'#{i}: Node {node_id}',
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)
        except:
            pass

    # Draw route lines using actual road network
    waypoints = [[depot_lon, depot_lat]]
    for node_id in route[1:]:
        if node_id == 0:
            waypoints.append([depot_lon, depot_lat])
        else:
            try:
                point = delivery_points.get(node_id=node_id)
                waypoints.append([point.longitude, point.latitude])
            except:
                pass

    # Try to get actual road geometry
    client = TomTomClient()
    # TomTom Calculate Route max waypoints is 150. We can send all at once.
    # However, to be safe we chunk by 140
    
    route_geometry = []
    chunk_size = 140
    for i in range(0, len(waypoints) - 1, chunk_size - 1):
        chunk = waypoints[i:i + chunk_size]
        geom = client.get_route_geometry(chunk)
        if geom:
            route_geometry.extend(geom)
    
    if route_geometry:
        folium.PolyLine(
            locations=route_geometry,
            color='#1628b0',
            weight=4,
            opacity=0.8,
            tooltip='Rute Dinamis (Jalan Umum)'
        ).add_to(m)
    else:
        # Fallback to straight lines
        route_coords = [[lat, lon] for lon, lat in waypoints]
        folium.PolyLine(
            locations=route_coords,
            color='#1628b0',
            weight=3,
            opacity=0.8,
            tooltip='Rute Lurus (Fallback)'
        ).add_to(m)

    return m._repr_html_()


def _get_dashboard_stats():
    """Helper: Compute shared dashboard statistics."""
    delivery_points = DeliveryPoint.objects.all()
    total_nodes = delivery_points.count()
    runs = OptimizationRun.objects.all()
    total_runs = runs.count()

    # Compute averages
    avg_feasibility = None
    avg_distance = None
    avg_time = None
    if total_runs > 0:
        feasibilities = [r.route_feasibility_pct for r in runs]
        distances = [r.total_distance_km for r in runs]
        times = [r.computation_time_sec for r in runs]
        avg_feasibility = round(sum(feasibilities) / len(feasibilities), 1)
        avg_distance = round(sum(distances) / len(distances), 2)
        avg_time = round(sum(times) / len(times), 2)

    # Package status (dummy distribution based on total_nodes)
    delivered = 0
    in_process = 0
    pending = total_nodes
    delivered_pct = 0
    in_process_pct = 0
    pending_pct = 100 if total_nodes > 0 else 0

    # Priority counts
    high_priority = delivery_points.filter(priority=1).count()
    blocked_roads = delivery_points.filter(road_status=False).count()
    open_roads = delivery_points.filter(road_status=True).count()
    high_priority_count = high_priority

    # Chart data for last 10 runs
    recent_runs_for_chart = runs[:10]
    run_labels = [r.created_at.strftime('%d/%m') for r in recent_runs_for_chart]
    aco_distances = [r.total_distance_km for r in recent_runs_for_chart]
    baseline_distances = []
    for r in recent_runs_for_chart:
        comp = r.comparisons.first()
        baseline_distances.append(comp.baseline_distance_km if comp else r.total_distance_km)

    return {
        'delivery_points': delivery_points,
        'total_nodes': total_nodes,
        'total_runs': total_runs,
        'avg_feasibility': avg_feasibility,
        'avg_distance': avg_distance,
        'avg_time': avg_time,
        'delivered': delivered,
        'in_process': in_process,
        'pending': pending,
        'delivered_pct': delivered_pct,
        'in_process_pct': in_process_pct,
        'pending_pct': pending_pct,
        'high_priority': high_priority,
        'blocked_roads': blocked_roads,
        'open_roads': open_roads,
        'high_priority_count': high_priority_count,
        'run_labels_json': json.dumps(run_labels),
        'aco_distances_json': json.dumps(aco_distances),
        'baseline_distances_json': json.dumps(baseline_distances),
    }


def dashboard(request):
    """Main dashboard view"""
    stats = _get_dashboard_stats()
    recent_runs = OptimizationRun.objects.all()[:5]
    stats['recent_runs'] = recent_runs
    return render(request, 'routing/dashboard.html', stats)


def generate_sample_data(request):
    """Generate sample delivery data"""
    if request.method == 'POST':
        form = GenerateSampleDataForm(request.POST)
        if form.is_valid():
            n_nodes = form.cleaned_data['n_nodes']
            seed = form.cleaned_data.get('seed', 42)

            # Clear existing data
            DeliveryPoint.objects.all().delete()

            # Generate sample data
            np.random.seed(seed)

            for i in range(1, n_nodes + 1):
                DeliveryPoint.objects.create(
                    node_id=i,
                    latitude=round(float(np.random.uniform(-7.19, -7.15)), 6),
                    longitude=round(float(np.random.uniform(112.58, 112.64)), 6),
                    demand=int(np.random.randint(1, 5)),
                    time_window_open='08:00',
                    time_window_close='17:00',
                    service_time=np.random.randint(3, 12),
                    priority=np.random.choice([1, 2, 3]),
                    road_status=np.random.choice([True, True, True, False])  # 25% blocked
                )

            messages.success(request, f'Berhasil generate {n_nodes} titik pengiriman!')

    # Redirect back to the referring page or dashboard
    referer = request.META.get('HTTP_REFERER', '')
    if 'data-paket' in referer or 'data_paket' in referer:
        return redirect('data_paket')
    if 'optimasi' in referer:
        return redirect('optimasi_rute')
    return redirect('dashboard')


def optimasi_rute(request):
    """Halaman Optimasi Rute — form parameter + peta"""
    depot_form = DepotForm()
    aco_form = ACOParametersForm()

    delivery_points = DeliveryPoint.objects.all()
    total_nodes = delivery_points.count()

    # Get latest run for map/stats display
    latest_run = OptimizationRun.objects.first()
    latest_map_html = None

    if latest_run and total_nodes > 0:
        try:
            latest_map_html = generate_route_map(
                latest_run.route_json,
                delivery_points,
                -7.16434,
                112.65168
            )
        except Exception:
            latest_map_html = None

    stats = _get_dashboard_stats()
    context = {
        'depot_form': depot_form,
        'aco_form': aco_form,
        'total_nodes': total_nodes,
        'latest_run': latest_run,
        'latest_map_html': latest_map_html,
        'blocked_roads': stats['blocked_roads'],
    }
    return render(request, 'routing/optimasi_rute.html', context)


def run_optimization(request):
    """Run ACO optimization"""
    if request.method == 'POST':
        depot_form = DepotForm(request.POST)
        aco_form = ACOParametersForm(request.POST)

        if depot_form.is_valid() and aco_form.is_valid():
            # Get parameters
            depot_lat = depot_form.cleaned_data['depot_latitude']
            depot_lon = depot_form.cleaned_data['depot_longitude']
            n_ants = aco_form.cleaned_data['n_ants']
            n_iterations = aco_form.cleaned_data['n_iterations']
            alpha = aco_form.cleaned_data['alpha']
            beta = aco_form.cleaned_data['beta']
            rho = aco_form.cleaned_data['rho']
            Q = aco_form.cleaned_data['Q']

            # Save depot coordinates to session for map generation
            request.session['depot_lat'] = depot_lat
            request.session['depot_lon'] = depot_lon

            # Get delivery points
            delivery_points = DeliveryPoint.objects.all()

            if delivery_points.count() == 0:
                messages.error(request, 'Tidak ada titik pengiriman. Silakan generate data terlebih dahulu.')
                return redirect('optimasi_rute')

            # Prepare data
            df = pd.DataFrame(list(delivery_points.values()))

            # Add depot
            depot_row = pd.DataFrame([{
                'node_id': 0,
                'latitude': depot_lat,
                'longitude': depot_lon,
                'demand': 0,
                'time_window_open': '00:00',
                'time_window_close': '23:59',
                'service_time': 0,
                'priority': 1,
                'road_status': True
            }])

            df_with_depot = pd.concat([depot_row, df], ignore_index=True)

            # Add time window in minutes
            df_with_depot['tw_open_min'] = 0
            df_with_depot['tw_close_min'] = 1440

            # Get travel time matrix (minutes)
            tomtom_client = TomTomClient()
            coords = [(row['longitude'], row['latitude']) for _, row in df_with_depot.iterrows()]
            distance_matrix = tomtom_client.get_distance_matrix(coords)

            # Run ACO
            start_time = time.time()
            aco = ACOOptimizer(n_ants=n_ants, n_iterations=n_iterations,
                               alpha=alpha, beta=beta, rho=rho, Q=Q)
            aco_route, aco_distance, convergence = aco.optimize(distance_matrix, df_with_depot)
            aco_time = time.time() - start_time

            # Run baseline
            baseline = NearestNeighborBaseline()
            nn_route, nn_distance = baseline.solve(distance_matrix, df_with_depot)

            # Evaluate
            evaluator = RouteEvaluator()
            comparison = evaluator.compare_algorithms(aco_route, nn_route, distance_matrix, df_with_depot)

            # Save to database
            opt_run = OptimizationRun.objects.create(
                algorithm='ACO',
                n_nodes=delivery_points.count(),
                total_distance_km=comparison['aco']['total_distance_km'],
                computation_time_sec=aco_time,
                time_window_violations=comparison['aco']['time_window_violations'],
                route_feasibility_pct=comparison['aco']['route_feasibility_pct'],
                parameters={'n_ants': n_ants, 'n_iterations': n_iterations, 'alpha': alpha, 'beta': beta, 'rho': rho, 'Q': Q},
                route_json=aco_route,
                notes=f'ACO optimization with {n_ants} ants and {n_iterations} iterations'
            )

            ComparisonResult.objects.create(
                optimization_run=opt_run,
                aco_distance_km=comparison['aco']['total_distance_km'],
                baseline_distance_km=comparison['baseline']['total_distance_km'],
                improvement_km=comparison['improvement_km'],
                improvement_pct=comparison['improvement_pct'],
                aco_better=comparison['aco_better']
            )

            # Store in session for result page
            request.session['latest_run_id'] = opt_run.id

            messages.success(request, f'Optimasi selesai dalam {aco_time:.2f} detik! Waktu tempuh: {comparison["aco"]["total_distance_km"]:.1f} Menit')
            return redirect('result')
        else:
            messages.error(request, 'Parameter tidak valid. Periksa kembali input Anda.')

    return redirect('optimasi_rute')


def result(request):
    """Show optimization result"""
    run_id = request.session.get('latest_run_id')

    if not run_id:
        # Try to get the latest run
        opt_run = OptimizationRun.objects.first()
        if not opt_run:
            messages.warning(request, 'Belum ada hasil optimasi. Jalankan optimasi terlebih dahulu.')
            return redirect('optimasi_rute')
    else:
        try:
            opt_run = OptimizationRun.objects.get(id=run_id)
        except OptimizationRun.DoesNotExist:
            opt_run = OptimizationRun.objects.first()
            if not opt_run:
                messages.warning(request, 'Hasil optimasi tidak ditemukan.')
                return redirect('optimasi_rute')

    comparison = opt_run.comparisons.first()

    # Generate Folium map
    delivery_points = DeliveryPoint.objects.all()
    depot_lat = request.session.get('depot_lat', -7.164340)  # Default Gresik
    depot_lon = request.session.get('depot_lon', 112.651680)

    try:
        map_html = generate_route_map(
            opt_run.route_json,
            delivery_points,
            depot_lat,
            depot_lon
        )
    except Exception as e:
        map_html = f'<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#6b7280;font-size:13px;">Gagal memuat peta: {str(e)}</div>'

    context = {
        'opt_run': opt_run,
        'comparison': comparison,
        'map_html': map_html
    }

    return render(request, 'routing/result.html', context)


def history(request):
    """Show optimization history"""
    runs = OptimizationRun.objects.all()[:20]

    context = {
        'runs': runs
    }

    return render(request, 'routing/history.html', context)


def data_paket(request):
    """Data Paket — tabel semua delivery points"""
    delivery_points = DeliveryPoint.objects.all()
    total = delivery_points.count()
    high_priority_count = delivery_points.filter(priority=1).count()
    open_roads = delivery_points.filter(road_status=True).count()

    # Average service time
    avg_service_time = None
    if total > 0:
        total_st = sum(p.service_time for p in delivery_points)
        avg_service_time = round(total_st / total, 1)

    context = {
        'delivery_points': delivery_points,
        'high_priority_count': high_priority_count,
        'open_roads': open_roads,
        'avg_service_time': avg_service_time,
    }
    return render(request, 'routing/data_paket.html', context)


def tambah_paket(request):
    """View untuk menambahkan paket pengiriman secara manual"""
    if request.method == 'POST':
        form = DeliveryPointForm(request.POST)
        if form.is_valid():
            # If node_id already exists, calculate a safe one, or just save
            # The form should handle unique constraints if any. 
            form.save()
            messages.success(request, 'Data paket berhasil ditambahkan!')
            return redirect('data_paket')
        else:
            messages.error(request, 'Gagal menambahkan paket. Periksa kembali data Anda.')
    else:
        # Default node ID is count + 1
        next_id = DeliveryPoint.objects.count() + 1
        # Default starting map location (Gresik)
        form = DeliveryPointForm(initial={
            'node_id': next_id,
            'latitude': -7.164340,
            'longitude': 112.651680,
            'demand': 1,
            'time_window_open': '08:00',
            'time_window_close': '17:00',
            'service_time': 5,
            'priority': 2,
            'road_status': True,
        })
        
    return render(request, 'routing/tambah_paket.html', {'form': form})


def live_map(request):
    """Live Map — stub page"""
    return render(request, 'routing/live_map.html')


def statistik(request):
    """Statistik — halaman analisis dengan data dasar"""
    stats = _get_dashboard_stats()
    return render(request, 'routing/statistik.html', stats)


def pengaturan(request):
    """Pengaturan — halaman konfigurasi sistem"""
    return render(request, 'routing/pengaturan.html')
