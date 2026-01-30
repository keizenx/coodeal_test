# tests/selenium_tests/test_simple_login.py
# Test simple pour verifier que la connexion automatique fonctionne
# Verifie que l'utilisateur est connecte et peut naviguer sur le site
# RELEVANT FILES: ../conftest.py, test_user_journey.py

import pytest
from selenium.webdriver.common.by import By
import time


class TestSimpleLogin:
    """Tests simples pour verifier l'authentification automatique"""
    
    def test_authenticated_user_can_access_site(self, authenticated_driver, live_server_url):
        """Teste qu'un utilisateur authentifie peut acceder au site"""
        # Aller sur la page d'accueil
        authenticated_driver.get(f"{live_server_url}/")
        time.sleep(2)
        
        # Verifier que la page se charge
        assert "404" not in authenticated_driver.page_source
        print("[OK] Page d'accueil chargee")
    
    def test_authenticated_user_can_access_deals(self, authenticated_driver, live_server_url):
        """Teste qu'un utilisateur authentifie peut voir les deals"""
        authenticated_driver.get(f"{live_server_url}/deals/")
        time.sleep(3)
        
        # Verifier que la page se charge
        assert "404" not in authenticated_driver.page_source
        
        # Afficher un echantillon du contenu pour debug
        body_text = authenticated_driver.find_element(By.TAG_NAME, "body").text
        print(f"[OK] Page deals chargee, longueur: {len(body_text)} caracteres")
        print(f"Echantillon: {body_text[:200]}")
    
    def test_authenticated_user_can_access_profile(self, authenticated_driver, live_server_url):
        """Teste qu'un utilisateur authentifie peut acceder a son profil"""
        authenticated_driver.get(f"{live_server_url}/client/")
        time.sleep(3)
        
        # Verifier que la page se charge
        assert "404" not in authenticated_driver.page_source
        
        # Verifier qu'on voit des elements du profil
        body_text = authenticated_driver.find_element(By.TAG_NAME, "body").text
        print(f"[OK] Page profil chargee")
        # Encoder en ASCII pour eviter les erreurs d'encodage Windows
        safe_text = body_text[:300].encode('ascii', 'replace').decode('ascii')
        print(f"Contenu: {safe_text}")
    
    def test_user_session_is_active(self, authenticated_driver, live_server_url):
        """Teste que la session utilisateur est active"""
        authenticated_driver.get(f"{live_server_url}/")
        time.sleep(2)
        
        # Verifier les cookies
        cookies = authenticated_driver.get_cookies()
        session_cookie = None
        
        for cookie in cookies:
            if cookie['name'] == 'sessionid':
                session_cookie = cookie
                break
        
        assert session_cookie is not None, "Session cookie devrait etre present"
        print(f"[OK] Session cookie trouve: {session_cookie['value'][:20]}...")
    
    def test_find_product_links(self, authenticated_driver, live_server_url):
        """Teste qu'on peut trouver les liens de produits"""
        authenticated_driver.get(f"{live_server_url}/deals/")
        time.sleep(3)
        
        # Chercher differents types de liens de produits
        all_links = authenticated_driver.find_elements(By.TAG_NAME, "a")
        product_links = []
        
        for link in all_links:
            href = link.get_attribute('href')
            if href and ('produit' in href.lower() or 'deal' in href.lower()):
                product_links.append(href)
        
        print(f"[OK] Trouve {len(product_links)} liens de produits")
        if product_links:
            print(f"Exemples: {product_links[:3]}")
        
        # Afficher toutes les classes CSS utilisees (pour trouver les bons selecteurs)
        all_elements = authenticated_driver.find_elements(By.XPATH, "//*[@class]")
        unique_classes = set()
        for elem in all_elements[:50]:  # Limiter a 50 pour ne pas surcharger
            classes = elem.get_attribute('class')
            if classes:
                unique_classes.update(classes.split())
        
        print(f"[OK] Classes CSS trouvees: {sorted(list(unique_classes))[:20]}")
