# tests/conftest.py
# Configuration globale Pytest pour tous les tests du projet
# Définit les fixtures communes (drivers Selenium, base de données de test, etc.)
# RELEVANT FILES: selenium_tests/conftest.py, performance_tests/conftest.py

import pytest
import os
import django
from django.conf import settings
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from django.contrib.auth.models import User
from customer.models import Customer

# Configuration Django pour les tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cooldeal.settings')
django.setup()


@pytest.fixture(scope='session')
def django_db_setup():
    """Configure la base de données pour les tests"""
    # Utiliser la vraie base de données SQLite pour les tests Selenium
    # Ne pas utiliser :memory: car les tests Selenium ont besoin de persistance
    pass


@pytest.fixture(scope='function')
def edge_driver():
    """
    Fixture pour créer et fermer le driver Edge Selenium
    Utilisé pour les tests fonctionnels
    """
    edge_options = Options()
    # edge_options.add_argument('--headless')  # Désactivé pour voir le browser
    edge_options.add_argument('--disable-gpu')
    edge_options.add_argument('--no-sandbox')
    edge_options.add_argument('--window-size=1920,1080')
    edge_options.add_argument('--disable-dev-shm-usage')
    edge_options.add_argument('--disable-extensions')
    edge_options.add_argument('--disable-logging')
    edge_options.add_argument('--log-level=3')
    
    # Chemin vers le driver Edge
    driver_path = r'C:\Users\Admin\Desktop\cod_test\msedgedriver.exe'
    service = Service(driver_path)
    
    driver = webdriver.Edge(service=service, options=edge_options)
    driver.implicitly_wait(5)
    
    # Définir des timeouts de page plus courts
    driver.set_page_load_timeout(15)
    driver.set_script_timeout(10)
    
    yield driver
    
    driver.quit()


@pytest.fixture(scope='function')
def authenticated_driver(edge_driver, live_server_url, db):
    """
    Fixture qui retourne un driver Edge avec un utilisateur déjà connecté.
    Se connecte via Vue.js pour obtenir une vraie session.
    """
    import time
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cooldeal.settings')
    django.setup()
    
    from django.contrib.auth.models import User
    from customer.models import Customer
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    # Aller sur la page de login
    edge_driver.get(f"{live_server_url}/customer/")
    
    try:
        # Attendre que Vue.js soit initialisé
        WebDriverWait(edge_driver, 10).until(
            lambda d: d.execute_script("""
                var loginDiv = document.querySelector('#login');
                return loginDiv && loginDiv.__vue__ ? true : false;
            """)
        )
        print("[OK] Vue.js initialise")
        
        # Remplir les champs via Vue.js directement
        edge_driver.execute_script("""
            var loginDiv = document.querySelector('#login');
            if (loginDiv && loginDiv.__vue__) {
                loginDiv.__vue__.username = 'keizen1';
                loginDiv.__vue__.password = 'fr@nckX75tyu';
            }
        """)
        
        time.sleep(0.5)
        
        # Appeler directement la méthode login de Vue.js
        edge_driver.execute_script("""
            var loginDiv = document.querySelector('#login');
            if (loginDiv && loginDiv.__vue__) {
                loginDiv.__vue__.login();
            }
        """)
        
        print("[OK] Methode login() appelee")
        
        # Attendre la redirection vers la page d'accueil
        time.sleep(3)
        
        current_url = edge_driver.current_url
        
        if '/customer/' not in current_url:
            print(f"[OK] Connexion reussie pour keizen1! URL: {current_url}")
        else:
            print(f"[WARN] Pas de redirection, URL: {current_url}")
            
    except Exception as e:
        print(f"[WARN] Erreur connexion: {str(e)[:150]}")
        print(f"URL actuelle: {edge_driver.current_url}")
    
    return edge_driver


@pytest.fixture(scope='function')
def live_server_url():
    """URL du serveur de développement Django"""
    return 'http://127.0.0.1:8000'


@pytest.fixture(scope='function')
def test_user_data():
    """Données de test pour un utilisateur"""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'Test@1234',
        'nom': 'Test',
        'prenoms': 'User',
        'phone': '0712345678',
        'adresse': 'Rue test Cocody',
    }


@pytest.fixture(scope='function')
def test_product_data():
    """Données de test pour un produit"""
    return {
        'nom': 'Test Deal Restaurant',
        'prix': 5000,
        'prix_promotionnel': 3000,
        'quantite': 10,
    }
