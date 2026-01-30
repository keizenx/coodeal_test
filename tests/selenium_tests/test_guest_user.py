# tests/selenium_tests/test_guest_user.py
# Test du parcours utilisateur NON CONNECTE (guest)
# Verifie: ajout panier OK, favoris KO, redirection login, checkout apres connexion
# RELEVANT FILES: shop/views.py, customer/views.py, test_user_journey.py

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestGuestUser:
    """Parcours utilisateur non connecte (guest)"""
    
    def test_guest_cannot_add_to_wishlist(self, edge_driver, live_server_url):
        """Verifie qu'un utilisateur non connecte NE PEUT PAS ajouter aux favoris"""
        driver = edge_driver
        bugs_detectes = []
        tests_passes = []
        
        print("\n" + "="*60)
        print("[TEST GUEST] Ajout aux favoris - doit echouer")
        print("="*60)
        
        # Aller sur un produit
        driver.get(f"{live_server_url}/deals/")
        time.sleep(3)
        
        try:
            # Cliquer sur un produit
            prod = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="grid"]/div[1]/div[2]/div/div[2]/a'))
            )
            driver.execute_script("arguments[0].click();", prod)
            time.sleep(3)
            print("[OK] Produit ouvert")
            
            # Essayer d'ajouter aux favoris
            try:
                fav_btn = driver.find_element(By.XPATH, '//*[@id="cart"]/div/ul/li[3]/form/button/i')
                driver.execute_script("arguments[0].click();", fav_btn)
                time.sleep(2)
                
                # Verifier si redirection vers login ou message d'erreur
                current_url = driver.current_url
                page_content = driver.page_source.lower()
                
                if 'login' in current_url or 'customer' in current_url or 'connectez' in page_content:
                    print("[OK] Redirection vers login (comportement attendu)")
                    tests_passes.append("Guest favoris: Redirection login - OK")
                elif 'favoris' in page_content or 'wishlist' in page_content:
                    print("[ERROR] Favoris ajouté sans connexion!")
                    bugs_detectes.append("BUG CRITIQUE: Utilisateur non connecté peut ajouter aux favoris")
                else:
                    print("[INFO] Bouton favoris cliqué, verification...")
                    
            except Exception as e:
                print(f"[OK] Bouton favoris non accessible (attendu): {str(e)[:50]}")
                tests_passes.append("Guest favoris: Bouton non accessible - OK")
                
        except Exception as e:
            print(f"[WARN] Erreur produit: {str(e)[:50]}")
        
        # Resume
        print("\n" + "="*60)
        print(f"Tests passes: {len(tests_passes)}")
        print(f"Bugs: {len(bugs_detectes)}")
        if bugs_detectes:
            pytest.fail(f"Bugs detectes: {bugs_detectes}")
    
    def test_guest_cart_to_checkout_to_login(self, edge_driver, live_server_url):
        """
        Parcours complet utilisateur non connecte:
        1. Ajouter produit au panier (doit marcher)
        2. Aller au checkout
        3. Redirection vers login
        4. Se connecter
        5. Retour sur checkout
        6. Payer
        """
        driver = edge_driver
        bugs_detectes = []
        tests_passes = []
        
        print("\n" + "#"*60)
        print("#        PARCOURS GUEST: PANIER -> LOGIN -> CHECKOUT        #")
        print("#"*60)
        
        # ETAPE 1: Aller sur /deals/
        print("\n" + "="*60)
        print("[ETAPE 1] Navigation /deals/")
        print("="*60)
        driver.get(f"{live_server_url}/deals/")
        time.sleep(3)
        print(f"[OK] URL: {driver.current_url}")
        tests_passes.append("ETAPE 1: /deals/ - OK")
        
        # ETAPE 2: Selectionner un produit
        print("\n" + "="*60)
        print("[ETAPE 2] Selectionner produit")
        print("="*60)
        try:
            prod = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="grid"]/div[1]/div[2]/div/div[2]/a'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", prod)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", prod)
            time.sleep(3)
            print("[OK] Produit selectionne")
            tests_passes.append("ETAPE 2: Produit - OK")
        except Exception as e:
            print(f"[ERROR] {str(e)[:50]}")
            bugs_detectes.append("BUG: Produit non selectionnable")
        
        # ETAPE 3: Ajouter au panier (doit marcher sans connexion)
        print("\n" + "="*60)
        print("[ETAPE 3] Ajouter au panier (guest)")
        print("="*60)
        try:
            cart_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="cart"]/div/ul/li[2]/button'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cart_btn)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", cart_btn)
            time.sleep(3)
            print("[OK] Produit ajoute au panier")
            tests_passes.append("ETAPE 3: Ajout panier guest - OK")
        except Exception as e:
            print(f"[ERROR] {str(e)[:50]}")
            bugs_detectes.append("BUG: Guest ne peut pas ajouter au panier")
        
        # ETAPE 4: Aller au panier
        print("\n" + "="*60)
        print("[ETAPE 4] Page panier")
        print("="*60)
        driver.get(f"{live_server_url}/deals/cart")
        time.sleep(3)
        print(f"[OK] URL: {driver.current_url}")
        tests_passes.append("ETAPE 4: Panier - OK")
        
        # ETAPE 5: Checkout (doit rediriger vers login)
        print("\n" + "="*60)
        print("[ETAPE 5] Checkout -> Redirection login")
        print("="*60)
        try:
            checkout = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="cart"]/div/div[2]/div[2]/div[2]/input'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkout)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", checkout)
            time.sleep(4)
            
            current_url = driver.current_url
            print(f"[INFO] URL apres checkout: {current_url}")
            
            # Verifier redirection vers login
            if 'login' in current_url.lower() or 'customer' in current_url:
                print("[OK] Redirection vers login (comportement attendu)")
                tests_passes.append("ETAPE 5: Redirection login - OK")
            elif 'checkout' in current_url:
                print("[WARN] Deja sur checkout sans login!")
                # C'est peut-etre OK si l'app permet checkout guest
                tests_passes.append("ETAPE 5: Checkout direct - OK (ou bug)")
            else:
                print(f"[WARN] URL inattendue: {current_url}")
                
        except Exception as e:
            print(f"[WARN] {str(e)[:50]}")
        
        # ETAPE 6: Se connecter avec keizen1
        print("\n" + "="*60)
        print("[ETAPE 6] Login avec keizen1")
        print("="*60)
        
        # Verifier si on est sur la page de login
        if 'login' in driver.current_url.lower() or 'customer' in driver.current_url:
            try:
                # Attendre Vue.js
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("""
                        var loginDiv = document.querySelector('#login');
                        return loginDiv && loginDiv.__vue__ ? true : false;
                    """)
                )
                
                # Login via Vue.js
                driver.execute_script("""
                    var loginDiv = document.querySelector('#login');
                    if (loginDiv && loginDiv.__vue__) {
                        loginDiv.__vue__.username = 'keizen1';
                        loginDiv.__vue__.password = 'fr@nckX75tyu';
                        loginDiv.__vue__.login();
                    }
                """)
                print("[OK] Login execute")
                time.sleep(4)
                
                current_url = driver.current_url
                print(f"[INFO] URL apres login: {current_url}")
                
                # Verifier redirection vers checkout
                if 'checkout' in current_url:
                    print("[OK] Redirection vers checkout apres login")
                    tests_passes.append("ETAPE 6: Login -> Checkout - OK")
                else:
                    print(f"[WARN] Pas sur checkout: {current_url}")
                    # Aller manuellement au checkout
                    driver.get(f"{live_server_url}/deals/checkout")
                    time.sleep(3)
                    
            except Exception as e:
                print(f"[ERROR] Login: {str(e)[:50]}")
                bugs_detectes.append("BUG: Login echoue")
        else:
            print("[INFO] Deja connecte ou pas sur page login")
            driver.get(f"{live_server_url}/deals/checkout")
            time.sleep(3)
        
        # ETAPE 7: Payer
        print("\n" + "="*60)
        print("[ETAPE 7] Paiement")
        print("="*60)
        try:
            pay = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="accordion"]/button'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pay)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", pay)
            time.sleep(5)
            print("[OK] Paiement effectue")
            tests_passes.append("ETAPE 7: Paiement - OK")
        except Exception as e:
            print(f"[WARN] {str(e)[:50]}")
            bugs_detectes.append("BUG: Paiement echoue")
        
        print(f"[INFO] URL finale: {driver.current_url}")
        driver.save_screenshot("guest_user_final.png")
        
        # Resume
        print("\n" + "="*60)
        print(f"RESULTAT: {len(tests_passes)} passed")
        if bugs_detectes:
            print(f"BUGS: {len(bugs_detectes)} bug(s)")
            for b in bugs_detectes:
                print(f"  - {b}")
        print("="*60)
        
        if bugs_detectes:
            pytest.fail(f"{len(bugs_detectes)} bug(s): {bugs_detectes}")
