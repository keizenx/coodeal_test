import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cooldeal.settings')
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

# Vérifier l'utilisateur
try:
    user = User.objects.get(username='keizen1')
    print(f"User trouvé: {user.username}, email: {user.email}")
    print(f"Is active: {user.is_active}")
except User.DoesNotExist:
    print("User keizen1 n'existe pas!")
    exit()

# Tester l'authentification
auth_user = authenticate(username='keizen1', password='fr@nckX75tyu')
if auth_user:
    print("✓ AUTHENTIFICATION REUSSIE")
else:
    print("✗ AUTHENTIFICATION ECHOUEE")
    
    # Essayer de reset le password
    print("\nReset du mot de passe...")
    user.set_password('fr@nckX75tyu')
    user.save()
    
    # Retester
    auth_user2 = authenticate(username='keizen1', password='fr@nckX75tyu')
    if auth_user2:
        print("✓ AUTHENTIFICATION REUSSIE après reset")
    else:
        print("✗ AUTHENTIFICATION TOUJOURS ECHOUEE")
