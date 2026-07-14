"""
Django Forms for Route Optimization
Form validation untuk input data pengiriman dan parameter PSO
"""

from django import forms
from .models import DeliveryPoint, OptimizationRun


class DeliveryPointForm(forms.ModelForm):
    """Form untuk input delivery point"""
    
    class Meta:
        model = DeliveryPoint
        fields = ['node_id', 'latitude', 'longitude', 'demand', 
                  'time_window_open', 'time_window_close', 'service_time', 
                  'priority', 'road_status']
        widgets = {
            'node_id': forms.NumberInput(attrs={'class': 'form-input rounded-lg border-gray-300'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-input rounded-lg border-gray-300', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-input rounded-lg border-gray-300', 'step': '0.000001'}),
            'demand': forms.NumberInput(attrs={'class': 'form-input rounded-lg border-gray-300'}),
            'time_window_open': forms.TextInput(attrs={'class': 'form-input rounded-lg border-gray-300', 'placeholder': 'HH:MM'}),
            'time_window_close': forms.TextInput(attrs={'class': 'form-input rounded-lg border-gray-300', 'placeholder': 'HH:MM'}),
            'service_time': forms.NumberInput(attrs={'class': 'form-input rounded-lg border-gray-300'}),
            'priority': forms.Select(attrs={'class': 'form-select rounded-lg border-gray-300'}),
            'road_status': forms.CheckboxInput(attrs={'class': 'form-checkbox rounded'}),
        }


class DepotForm(forms.Form):
    """Form untuk koordinat depot"""
    depot_latitude = forms.FloatField(
        initial=-7.164340,
        widget=forms.NumberInput(attrs={
            'class': 'form-input rounded-lg border-gray-300 w-full',
            'step': '0.000001',
            'placeholder': 'e.g., -7.164340'
        }),
        label='Depot Latitude'
    )
    depot_longitude = forms.FloatField(
        initial=112.651680,
        widget=forms.NumberInput(attrs={
            'class': 'form-input rounded-lg border-gray-300 w-full',
            'step': '0.000001',
            'placeholder': 'e.g., 112.651680'
        }),
        label='Depot Longitude'
    )


class PSOParametersForm(forms.Form):
    """Form untuk parameter PSO"""
    n_particles = forms.IntegerField(
        initial=20,
        min_value=5,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-input rounded-lg border-gray-300 w-full',
            'placeholder': '10-100'
        }),
        label='Number of Particles',
        help_text='Jumlah particles dalam populasi (recommended: 20)'
    )
    
    n_iterations = forms.IntegerField(
        initial=200,
        min_value=50,
        max_value=500,
        widget=forms.NumberInput(attrs={
            'class': 'form-input rounded-lg border-gray-300 w-full',
            'placeholder': '50-500'
        }),
        label='Maximum Iterations',
        help_text='Jumlah iterasi maksimum (recommended: 200)'
    )


class GenerateSampleDataForm(forms.Form):
    """Form untuk generate sample data"""
    n_nodes = forms.IntegerField(
        initial=30,
        min_value=10,
        max_value=50,
        widget=forms.NumberInput(attrs={
            'class': 'form-input rounded-lg border-gray-300 w-full',
            'placeholder': '10-50'
        }),
        label='Number of Delivery Points',
        help_text='Jumlah titik pengiriman untuk di-generate (10-50 nodes)'
    )
    
    seed = forms.IntegerField(
        initial=42,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-input rounded-lg border-gray-300 w-full',
            'placeholder': 'Random seed (optional)'
        }),
        label='Random Seed (Optional)',
        help_text='Untuk reproducible results'
    )


class CSVUploadForm(forms.Form):
    """Form untuk upload CSV file"""
    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-input rounded-lg border-gray-300 w-full',
            'accept': '.csv'
        }),
        label='Upload CSV File',
        help_text='Upload file CSV dengan format sesuai template'
    )
