import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dekouway.settings')
django.setup()

from django.contrib.auth import get_user_model
from properties.models import Property, PropertyImage, Amenity
from bookings.models import Booking
from django.core.files.base import ContentFile
import datetime

User = get_user_model()

def seed():
    print("--- Début du peuplement de la base de données ---")

    # 1. Create standard amenities
    amenity_data = [
        ('Wi-Fi', 'wifi'),
        ('Climatisation', 'wind'),
        ('Piscine', 'pocket'),
        ('Parking Gratuit', 'car'),
        ('Gardiennage 24h', 'shield'),
        ('Cuisine Équipée', 'utensils-crossringed'),
        ('Eau Chaude', 'thermometer'),
        ('Télévision', 'tv')
    ]
    amenities = {}
    for name, icon in amenity_data:
        amenity, created = Amenity.objects.get_or_create(name=name, defaults={'icon': icon})
        amenities[name] = amenity
        if created:
            print(f"Équipement créé : {name}")

    # 2. Create demo users
    # SuperAdmin
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@dekouway.sn',
            'first_name': 'Amadou',
            'last_name': 'Ndiaye',
            'role': 'admin',
            'is_superuser': True,
            'is_staff': True
        }
    )
    if created:
        admin_user.set_password('admin1234')
        admin_user.save()
        print("SuperAdmin 'admin' créé avec le mot de passe : admin1234")

    # Verified Owner
    owner_verified, created = User.objects.get_or_create(
        username='diop_owner',
        defaults={
            'email': 'diop@owner.sn',
            'first_name': 'Ibrahima',
            'last_name': 'Diop',
            'role': 'owner',
            'phone': '+221 77 111 22 33',
            'owner_status': 'approved',
            'is_verified_owner': True
        }
    )
    if created:
        owner_verified.set_password('owner1234')
        owner_verified.save()
        print("Propriétaire validé 'diop_owner' créé avec le mot de passe : owner1234")

    # Pending Owner
    owner_pending, created = User.objects.get_or_create(
        username='fatou_owner',
        defaults={
            'email': 'fatou@owner.sn',
            'first_name': 'Fatou',
            'last_name': 'Sow',
            'role': 'owner',
            'phone': '+221 78 444 55 66',
            'owner_status': 'pending',
            'is_verified_owner': False
        }
    )
    if created:
        owner_pending.set_password('owner1234')
        owner_pending.save()
        print("Propriétaire en attente 'fatou_owner' créé avec le mot de passe : owner1234")

    # Client
    client_user, created = User.objects.get_or_create(
        username='moustapha_client',
        defaults={
            'email': 'moustapha@client.sn',
            'first_name': 'Moustapha',
            'last_name': 'Gaye',
            'role': 'client',
            'phone': '+221 77 999 88 77',
            'owner_status': 'approved',
            'is_verified_owner': False
        }
    )
    if created:
        client_user.set_password('client1234')
        client_user.save()
        print("Client 'moustapha_client' créé avec le mot de passe : client1234")

    # Create dummy image for listings
    dummy_img_dir = os.path.join('media', 'properties')
    os.makedirs(dummy_img_dir, exist_ok=True)
    dummy_img_path = os.path.join(dummy_img_dir, 'dummy_home.jpg')
    if not os.path.exists(dummy_img_path):
        # A valid tiny 1x1 pixel JPEG file binary representation
        tiny_jpeg = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x0f\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xc4\x00\x10\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x01\x01\x00\x02\x11\x03\x11\x00?\x00\xa0\xff\xd9'
        with open(dummy_img_path, 'wb') as f:
            f.write(tiny_jpeg)
        print("Dummy JPEG file written under media/properties/dummy_home.jpg")

    # 3. Create sample properties
    properties_data = [
        {
            'title': 'Splendide Villa Keur Thiossane avec Piscine',
            'description': 'Venez séjourner dans cette magnifique villa contemporaine de haut standing située aux Almadies. Elle dispose d\'une grande piscine privée, d\'un grand salon lumineux, de 3 chambres spacieuses climatisées et d\'une sécurité assurée H24. Proche de toutes commodités et de la plage.',
            'property_type': 'villa',
            'price_per_night': 120000,
            'address': 'Rue des Almadies, Zone 10',
            'city': 'Dakar',
            'neighborhood': 'Almadies',
            'latitude': 14.7454,
            'longitude': -17.5143,
            'capacity': 6,
            'bedrooms': 3,
            'bathrooms': 4,
            'status': 'approved',
            'is_available': True,
            'amenity_list': ['Wi-Fi', 'Climatisation', 'Piscine', 'Parking Gratuit', 'Gardiennage 24h', 'Cuisine Équipée', 'Eau Chaude', 'Télévision']
        },
        {
            'title': 'Appartement de Standing Fann Résidence',
            'description': 'Superbe appartement de 2 chambres situé dans le quartier calme et sécurisé de Fann Résidence. Idéal pour vos séjours professionnels ou en famille. Vue imprenable sur la mer, balcon filant, cuisine moderne entièrement équipée et gardiennage 24/7.',
            'property_type': 'apartment',
            'price_per_night': 75000,
            'address': 'Avenue Cheikh Anta Diop',
            'city': 'Dakar',
            'neighborhood': 'Fann Résidence',
            'latitude': 14.6932,
            'longitude': -17.4729,
            'capacity': 4,
            'bedrooms': 2,
            'bathrooms': 2,
            'status': 'approved',
            'is_available': True,
            'amenity_list': ['Wi-Fi', 'Climatisation', 'Gardiennage 24h', 'Cuisine Équipée', 'Eau Chaude', 'Télévision']
        },
        {
            'title': 'Studio Cosy tout équipé à Ngor',
            'description': 'Joli studio meublé chaleureux et fonctionnel situé au cœur de Ngor. Parfait pour les couples ou voyageurs en solo. Proche du débarcadère pour l\'île de Ngor, des restaurants, des supermarchés et des transports.',
            'property_type': 'studio',
            'price_per_night': 25000,
            'address': 'Ngor Route de la Plage',
            'city': 'Dakar',
            'neighborhood': 'Ngor',
            'latitude': 14.7485,
            'longitude': -17.5098,
            'capacity': 2,
            'bedrooms': 1,
            'bathrooms': 1,
            'status': 'approved',
            'is_available': True,
            'amenity_list': ['Wi-Fi', 'Climatisation', 'Cuisine Équipée', 'Eau Chaude', 'Télévision']
        },
        {
            'title': 'Chambre d\'hôte Teranga Saly',
            'description': 'Chambre tout confort avec salle de bain privée dans une magnifique résidence verdoyante à Saly Portudal. Accès direct à la plage, piscine partagée, petit-déjeuner inclus et accueil Teranga exceptionnel.',
            'property_type': 'room',
            'price_per_night': 35000,
            'address': 'Résidence du Port Saly',
            'city': 'Saly',
            'neighborhood': 'Saly Portudal',
            'latitude': 14.4412,
            'longitude': -16.9856,
            'capacity': 2,
            'bedrooms': 1,
            'bathrooms': 1,
            'status': 'approved',
            'is_available': True,
            'amenity_list': ['Wi-Fi', 'Piscine', 'Parking Gratuit', 'Gardiennage 24h', 'Télévision']
        },
        {
            'title': 'Villa Baobab Sauvage Somone (Modération)',
            'description': 'Grande villa familiale en attente de modération, idéalement placée près de la lagune de la Somone. Idéale pour se ressourcer en pleine nature.',
            'property_type': 'villa',
            'price_per_night': 90000,
            'address': 'Piste de la Lagune',
            'city': 'Somone',
            'neighborhood': 'Somone',
            'latitude': 14.4820,
            'longitude': -17.0210,
            'capacity': 8,
            'bedrooms': 4,
            'bathrooms': 3,
            'status': 'pending',
            'is_available': True,
            'amenity_list': ['Wi-Fi', 'Piscine', 'Parking Gratuit']
        }
    ]

    for pdata in properties_data:
        amenity_list = pdata.pop('amenity_list')
        p_obj, created = Property.objects.get_or_create(
            title=pdata['title'],
            defaults={
                'owner': owner_verified,
                'description': pdata['description'],
                'property_type': pdata['property_type'],
                'price_per_night': pdata['price_per_night'],
                'address': pdata['address'],
                'city': pdata['city'],
                'neighborhood': pdata['neighborhood'],
                'latitude': pdata['latitude'],
                'longitude': pdata['longitude'],
                'capacity': pdata['capacity'],
                'bedrooms': pdata['bedrooms'],
                'bathrooms': pdata['bathrooms'],
                'status': pdata['status'],
                'is_available': pdata['is_available']
            }
        )
        if created:
            # Set amenities
            for name in amenity_list:
                p_obj.amenities.add(amenities[name])
            
            # Associate mock image
            PropertyImage.objects.create(
                property=p_obj,
                image='properties/dummy_home.jpg',
                is_main=True
            )
            print(f"Logement créé : {p_obj.title}")

    print("--- Peuplement terminé avec succès ! ---")

if __name__ == '__main__':
    seed()
