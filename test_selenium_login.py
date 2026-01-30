# test_selenium_login.py
# Script Selenium indépendant pour tester le login avec keizen1
# Ce script teste le formulaire de login de l'application Cooldeal
# RELEVANT FILES: customer/templates/login.html, customer/views.py

import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_login():
    """Test le login avec l'utilisateur keizen1"""
    
    # Configurer le driver Edge
    edge_options = Options()
    edge_options.add_argument('--disable-gpu')
    edge_options.add_argument('--no-sandbox')
    edge_options.add_argument('--window-size=1920,1080')
    
    driver_path = r'C:\Users\Admin\Desktop\cod_test\msedgedriver.exe'
    service = Service(driver_path)
    
    driver = webdriver.Edge(service=service, options=edge_options)
    driver.implicitly_wait(10)
    
    try:
        # Aller sur la page de login
        print("1. Ouverture de la page de login...")
        driver.get('http://127.0.0.1:8000/customer/')
        
        # Attendre que la page soit chargée
        time.sleep(2)
        
        # Vérifier que Vue.js est initialisé
        vue_ready = driver.execute_script("""
            var loginDiv = document.querySelector('#login');
            return loginDiv && loginDiv.__vue__ ? true : false;
        """)
        print(f"2. Vue.js initialisé: {vue_ready}")
        
        # Remplir les champs via Vue.js directement
        print("3. Remplissage des champs via Vue.js...")
        driver.execute_script("""
            var loginDiv = document.querySelector('#login');
            if (loginDiv && loginDiv.__vue__) {
                loginDiv.__vue__.username = 'keizen1';
                loginDiv.__vue__.password = 'fr@nckX75tyu';
            }
        """)
        
        # Attendre un peu pour que Vue.js réagisse
        time.sleep(1)
        
        # Vérifier les valeurs
        vue_data = driver.execute_script("""
            var loginDiv = document.querySelector('#login');
            if (loginDiv && loginDiv.__vue__) {
                return {
                    username: loginDiv.__vue__.username,
                    password: loginDiv.__vue__.password,
                    isregister: loginDiv.__vue__.isregister
                };
            }
            return {error: 'Vue not found'};
        """)
        print(f"4. Données Vue.js: username={vue_data.get('username')}, password_len={len(vue_data.get('password', ''))}")
        
        # Appeler directement la méthode login de Vue.js
        print("5. Appel de la méthode login de Vue.js...")
        driver.execute_script("""
            var loginDiv = document.querySelector('#login');
            if (loginDiv && loginDiv.__vue__) {
                loginDiv.__vue__.login();
            }
        """)
        
        # Attendre la réponse
        time.sleep(3)
        
        # Vérifier le résultat
        current_url = driver.current_url
        print(f"6. URL actuelle: {current_url}")
        
        # Si on a été redirigé vers la page d'accueil, la connexion a réussi
        if '/customer/' not in current_url:
            print("✓ CONNEXION RÉUSSIE! (Redirection vers page d'accueil)")
            return True
        
        # Sinon vérifier les messages Vue.js
        result = driver.execute_script("""
            var loginDiv = document.querySelector('#login');
            if (loginDiv && loginDiv.__vue__) {
                return {
                    isSuccess: loginDiv.__vue__.isSuccess,
                    error: loginDiv.__vue__.error,
                    message: loginDiv.__vue__.message
                };
            }
            return {error: 'Vue not found'};
        """)
        
        print(f"7. Résultat Vue.js: {result}")
        
        if result.get('isSuccess'):
            print("✓ CONNEXION RÉUSSIE!")
            return True
        elif result.get('error'):
            print(f"✗ ERREUR: {result.get('message')}")
            return False
        else:
            print(f"? État incertain: {result}")
            return False
            
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False
    
    finally:
        time.sleep(2)
        driver.quit()


if __name__ == '__main__':
    print("=" * 50)
    print("TEST SELENIUM LOGIN - keizen1")
    print("=" * 50)
    print()
    success = test_login()
    print()
    print("=" * 50)
    print(f"Résultat final: {'SUCCÈS' if success else 'ÉCHEC'}")
    print("=" * 50)
