"""
Django Views for Route Optimization System
Request handlers untuk dashboard, optimization, dan results
Menggunakan ACO (Ant Colony Optimization) sesuai Bab III paper
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import OptimizationRun, ComparisonResult, DeliveryPoint
from .forms import DepotForm, ACOParametersForm, GenerateSampleDataForm
from .ai_core.aco_optimizer import ACOOptimizer
from .ai_core.baseline_nn import NearestNeighborBaseline
from .ai_core.osrm_client import OSRMClient
from .ai_core.evaluator import RouteEvaluator
import pandas as pd
import numpy as np
import time
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
    
    # Draw route lines
    route_coords = [[depot_lat, depot_lon]]
    for node_id in route[1:]:
        if node_id == 0:
            route_coords.append([depot_lat, depot_lon])
        else:
            try:
                point = delivery_points.get(node_id=node_id)
                route_coords.append([point.latitude, point.longitude])
            except:
                pass
    
    folium.PolyLine(
        locations=route_coords,
        color='green',
        weight=3,
        opacity=0.7,
        tooltip='Optimized Route'
    ).add_to(m)
    
    return m._repr_html_()


def dashboard(request):
    """Main dashboard view"""
    depot_form = DepotForm()
    aco_form = ACOParametersForm()
    sample_form = GenerateSampleDataForm()
    
    # Get existing delivery points
    delivery_points = DeliveryPoint.objects.all()
    
    context = {
        'depot_form': depot_form,
        'aco_form': aco_form,
        'sample_form': sample_form,
        'delivery_points': delivery_points,
        'total_nodes': delivery_points.count()
    }
    
    return render(request, 'routing/dashboard.html', context)


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
                    latitude=np.random.uniform(-7.35, -7.10),
                    longitude=np.random.uniform(112.55, 112.75),
                    demand=np.random.randint(1, 6),
                    time_window_open='08:00',
                    time_window_close='17:00',
                    service_time=np.random.randint(3, 12),
                    priority=np.random.choice([1, 2, 3]),
                    road_status=True
                )
            
            messages.success(request, f'Successfully generated {n_nodes} delivery points!')
    
    return redirect('dashboard')


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
                messages.error(request, 'No delivery points available. Please generate or upload data first.')
                return redirect('dashboard')
            
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
            
            # Get distance matrix
            osrm_client = OSRMClient()
            coords = [(row['longitude'], row['latitude']) for _, row in df_with_depot.iterrows()]
            distance_matrix = osrm_client.get_distance_matrix(coords)
            
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
            
            messages.success(request, f'Optimization completed in {aco_time:.2f} seconds!')
            return redirect('result')
    
    return redirect('dashboard')


def result(request):
    """Show optimization result"""
    run_id = request.session.get('latest_run_id')
    
    if not run_id:
        messages.warning(request, 'No optimization results available.')
        return redirect('dashboard')
    
    opt_run = OptimizationRun.objects.get(id=run_id)
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
        map_html = f'<p class="text-red-500">Error generating map: {str(e)}</p>'
    
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
