# Script temporaire pour créer l'utilisateur de test keizen
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cooldeal.settings')
django.setup()

from django.contrib.auth.models import User
from customer.models import Customer
from cities_light.models import City

# Créer ou mettre à jour l'utilisateur keizen
try:
    user = User.objects.get(username='keizen')
    user.set_password('fr@nckX75tyu')
    user.save()
    print(f"✓ Utilisateur 'keizen' mis à jour")
except User.DoesNotExist:
    user = User.objects.create_user(
        username='keizen',
        email='keizen@test.com',
        password='fr@nckX75tyu',
        first_name='Keizen',
        last_name='Test'
    )
    print(f"✓ Utilisateur 'keizen' créé")

# Créer le profil Customer si nécessaire
try:
    customer = user.customer
    print(f"✓ Profil Customer existe déjà")
except Customer.DoesNotExist:
    city = City.objects.filter(name__icontains='Abidjan').first()
    if not city:
        city = City.objects.first()
    
    customer = Customer.objects.create(
        user=user,
        adresse='Cocody, Abidjan',
        contact_1='0501981186',
        ville=city,
        pays='Côte d\'Ivoire'
    )
    print(f"✓ Profil Customer créé")

# Ajouter une photo de profil si disponible
photo_path = r'C:\Users\Admin\Desktop\cod_test\Hacking_eth.webp'
if os.path.exists(photo_path) and not customer.photo:
    from django.core.files import File
    with open(photo_path, 'rb') as f:
        customer.photo.save('keizen_profile.webp', File(f), save=True)
    print(f"✓ Photo de profil ajoutée")

print(f"\n✅ Utilisateur de test prêt:")
print(f"   Username: keizen")
print(f"   Password: fr@nckX75tyu")
print(f"   Email: {user.email}")
