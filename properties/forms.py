from django import forms
from .models import Property, Amenity

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = (
            'title', 'description', 'property_type', 'price_per_night',
            'address', 'city', 'neighborhood', 'latitude', 'longitude',
            'capacity', 'bedrooms', 'bathrooms', 'amenities', 'is_available'
        )
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700', 'rows': 4}),
            'property_type': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700'}),
            'price_per_night': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700'}),
            'address': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700'}),
            'city': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700'}),
            'neighborhood': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700'}),
            'latitude': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700', 'step': 'any'}),
            'capacity': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700'}),
            'bedrooms': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700'}),
            'bathrooms': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700'}),
            'amenities': forms.CheckboxSelectMultiple(),
            'is_available': forms.CheckboxInput(attrs={'class': 'rounded text-primary-600 focus:ring-primary-500'}),
        }
