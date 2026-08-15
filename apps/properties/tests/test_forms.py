from django.test import SimpleTestCase
from apps.properties.forms import SearchForm, PropertyForm

class PropertiesFormsTestCase(SimpleTestCase):
    def test_search_form_valid(self):
        form = SearchForm(data={
            'q': 'Villa',
            'city': 'Dakar',
            'district': 'Almadies',
            'min_price': 20000,
            'max_price': 100000,
            'bedrooms': 2,
            'bathrooms': 1,
            'surface': 50,
            'property_type': 'villa',
            'equipments': 'Piscine, Wifi',
            'sort_by': 'newest'
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['city'], 'Dakar')
        self.assertEqual(form.cleaned_data['min_price'], 20000)

    def test_search_form_price_range_invalid(self):
        form = SearchForm(data={'min_price': 100000, 'max_price': 50000})
        self.assertFalse(form.is_valid())
        self.assertIn('Le prix minimum ne peut pas être supérieur au prix maximum.', form.non_field_errors())

    def test_property_form_valid(self):
        form = PropertyForm(data={
            'title': 'Villa Keur Thiossane',
            'description': 'Superbe villa avec piscine aux Almadies',
            'price': 120000,
            'pricing_period': 'NIGHTLY',
            'address': 'Rue 10 x Rue 12 Almadies',
            'city': 'Dakar',
            'district': 'Almadies',
            'latitude': 14.745400,
            'longitude': -17.514300,
            'surface': 200,
            'bedrooms': 3,
            'bathrooms': 2,
            'max_guests': 6,
            'property_type_id': 'type_123',
        })
        self.assertTrue(form.is_valid())

    def test_property_form_defaults_pricing_period_when_omitted(self):
        form = PropertyForm(data={
            'title': 'Villa Keur Thiossane',
            'description': 'Superbe villa avec piscine aux Almadies',
            'price': 120000,
            'address': 'Rue 10 x Rue 12 Almadies',
            'city': 'Dakar',
            'district': 'Almadies',
            'surface': 200,
            'bedrooms': 3,
            'bathrooms': 2,
            'max_guests': 6,
            'property_type_id': 'type_123',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['pricing_period'], 'NIGHTLY')

    def test_property_form_price_invalid(self):
        form = PropertyForm(data={
            'title': 'Villa Keur Thiossane',
            'description': 'Superbe villa avec piscine',
            'price': -500,
            'address': 'Rue 10',
            'city': 'Dakar',
            'district': 'Almadies',
            'surface': 200,
            'bedrooms': 3,
            'bathrooms': 2,
            'max_guests': 6,
            'property_type_id': 'type_123'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)

    def test_property_form_invalid_coordinates(self):
        form = PropertyForm(data={
            'title': 'Villa Keur Thiossane',
            'description': 'Superbe villa avec piscine',
            'price': 120000,
            'address': 'Rue 10',
            'city': 'Dakar',
            'district': 'Almadies',
            'latitude': 150.0,  # Invalid latitude > 90
            'longitude': -17.514300,
            'surface': 200,
            'bedrooms': 3,
            'bathrooms': 2,
            'max_guests': 6,
            'property_type_id': 'type_123'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('latitude', form.errors)

