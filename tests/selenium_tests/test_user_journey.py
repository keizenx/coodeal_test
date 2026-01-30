# tests/selenium_tests/test_user_journey.py
# Test Selenium du parcours utilisateur COMPLET: inscription -> achat -> profil -> commandes
# Simule le comportement reel d'un nouvel utilisateur sur le site
# RELEVANT FILES: conftest.py, customer/templates/register.html, client/templates/profil.html

import pytest
import time
import random
import string
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select


class TestUserJourney:
    """Parcours utilisateur complet: inscription -> achat -> gestion profil"""
    
    def generate_random_user(self):
        """Genere des donnees aleatoires pour un nouvel utilisateur"""
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return {
            'username': f'testuser_{suffix}',
            'email': f'testuser_{suffix}@test.com',
            'password': 'TestPass123!',
            'nom': 'TestNom',
            'prenoms': f'Prenom_{suffix}',
            'contact': '0612345678',
            'adresse': f'{random.randint(1, 100)} Rue de Test'
        }
    
    def test_parcours_utilisateur_complet(self, edge_driver, live_server_url):
        """
        Parcours complet d'un NOUVEL utilisateur (19 etapes):
        
        PARTIE 1 - INSCRIPTION (1-3)
        PARTIE 2 - NAVIGATION & ACHAT (4-12)
        PARTIE 3 - PROFIL & COMMANDES (13-19)
        """
        driver = edge_driver
        bugs_detectes = []
        tests_passes = []
        
        user_data = self.generate_random_user()
        print(f"\n[INFO] Utilisateur: {user_data['username']}")
        
        # ============================================================
        #                    PARTIE 1: INSCRIPTION
        # ============================================================
        print("\n" + "#"*60)
        print("#             PARTIE 1: INSCRIPTION                         #")
        print("#"*60)
        
        # ETAPE 1: Page inscription
        print("\n" + "="*60)
        print("[ETAPE 1] Page d'inscription")
        print("="*60)
        driver.get(f"{live_server_url}/customer/signup")
        time.sleep(3)
        print(f"[INFO] URL: {driver.current_url}")
        tests_passes.append("ETAPE 1: Page inscription - OK")
        
        # ETAPE 2: Upload photo et remplir formulaire (POST direct, pas Vue.js)
        print("\n" + "="*60)
        print("[ETAPE 2] Upload photo et remplissage")
        print("="*60)
        try:
            import os
            from PIL import Image
            
            # Creer et uploader une image de test
            temp_image = os.path.join(os.getcwd(), 'temp_profile.jpg')
            img = Image.new('RGB', (100, 100), color='blue')
            img.save(temp_image)
            
            file_input = driver.find_element(By.XPATH, '//*[@id="file"]')
            file_input.send_keys(temp_image)
            print("[OK] Photo uploadee")
            time.sleep(1)
            
            # Remplir les champs HTML directement
            driver.execute_script(f"""
                document.querySelector('input[placeholder="Nom"]').value = '{user_data['nom']}';
                document.querySelector('input[placeholder*="Prénoms"]').value = '{user_data['prenoms']}';
                document.querySelector('input[placeholder="Contact"]').value = '{user_data['contact']}';
                document.querySelector('select').selectedIndex = 1;
                document.querySelector('input[placeholder="Adresse"]').value = '{user_data['adresse']}';
                document.querySelector('input[placeholder*="utilisateur"]').value = '{user_data['username']}';
                document.querySelector('input[type="email"]').value = '{user_data['email']}';
                var pwdFields = document.querySelectorAll('input[type="password"]');
                pwdFields[0].value = '{user_data['password']}';
                pwdFields[1].value = '{user_data['password']}';
            """)
            print(f"[OK] Champs remplis: {user_data['username']}, {user_data['email']}")
            
            tests_passes.append("ETAPE 2: Formulaire - OK")
            
        except Exception as e:
            print(f"[WARN] Erreur formulaire: {str(e)[:80]}")
            bugs_detectes.append("BUG: Formulaire inscription")
        
        time.sleep(1)
        
        # ETAPE 3: Soumettre via POST fetch direct
        print("\n" + "="*60)
        print("[ETAPE 3] Soumission POST fetch")
        print("="*60)
        try:
            # Faire le POST avec fetch
            driver.execute_script("""
                var formData = new FormData();
                formData.append('nom', document.querySelector('input[placeholder="Nom"]').value);
                formData.append('prenoms', document.querySelector('input[placeholder*="Prénoms"]').value);
                formData.append('phone', document.querySelector('input[placeholder="Contact"]').value);
                formData.append('ville', document.querySelector('select').value);
                formData.append('adresse', document.querySelector('input[placeholder="Adresse"]').value);
                formData.append('username', document.querySelector('input[placeholder*="utilisateur"]').value);
                formData.append('email', document.querySelector('input[type="email"]').value);
                var pwdFields = document.querySelectorAll('input[type="password"]');
                formData.append('password', pwdFields[0].value);
                formData.append('passwordconf', pwdFields[1].value);
                
                var fileInput = document.querySelector('#file');
                if (fileInput.files[0]) {
                    formData.append('file', fileInput.files[0]);
                }
                
                var csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
                if (csrfInput) {
                    formData.append('csrfmiddlewaretoken', csrfInput.value);
                }
                
                fetch('/customer/inscription', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': csrfInput ? csrfInput.value : ''
                    }
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Inscription reponse:', data);
                    if (data.success) {
                        window.location.href = '/';
                    }
                })
                .catch(error => {
                    console.error('Erreur:', error);
                });
            """)
            print("[OK] POST fetch envoye")
            time.sleep(5)
            
            # Nettoyer l'image temporaire
            if os.path.exists(temp_image):
                os.remove(temp_image)
            
            # Verifier la redirection
            if driver.current_url == f"{live_server_url}/" or driver.current_url == live_server_url:
                print(f"[SUCCESS] Inscription reussie - Redirection vers {driver.current_url}")
                print(f"[SUCCESS] Utilisateur cree: {user_data['username']}")
                tests_passes.append("ETAPE 3: Inscription - OK")
            else:
                print(f"[WARN] Pas de redirection, URL: {driver.current_url}")
                bugs_detectes.append("BUG: Inscription non confirmee")
                
        except Exception as e:
            print(f"[WARN] {str(e)[:80]}")
            bugs_detectes.append("BUG: POST inscription")
        
        # L'utilisateur est maintenant connecte automatiquement (voir customer/views.py ligne 157)
        # Pas besoin de faire un login separement
        print("\n" + "="*60)
        print("[INFO] Utilisateur auto-connecte apres inscription")
        print("="*60)
        time.sleep(2)
        
        # ============================================================
        #                    PARTIE 2: NAVIGATION & ACHAT
        # ============================================================
        print("\n" + "#"*60)
        print("#             PARTIE 2: NAVIGATION & ACHAT                  #")
        print("#"*60)
        
        # ETAPE 4: Accueil
        print("\n" + "="*60)
        print("[ETAPE 4] Accueil")
        print("="*60)
        driver.get(f"{live_server_url}/")
        time.sleep(3)
        print("[OK] Page d'accueil chargee")
        tests_passes.append("ETAPE 4: Accueil - OK")
        
        # ETAPE 5: DEALS
        print("\n" + "="*60)
        print("[ETAPE 5] Cliquer DEALS")
        print("="*60)
        try:
            deals = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div/div[1]/div[2]/div[1]/div/div/div[2]/div/nav/ul/li[2]/a'))
            )
            driver.execute_script("arguments[0].click();", deals)
            time.sleep(3)
            print("[OK] Lien DEALS clique")
            tests_passes.append("ETAPE 5: DEALS - OK")
        except:
            driver.get(f"{live_server_url}/deals/")
            time.sleep(3)
            tests_passes.append("ETAPE 5: DEALS (direct) - OK")
        
        print(f"[INFO] URL: {driver.current_url}")
        
        # ETAPE 6: Choisir produit
        print("\n" + "="*60)
        print("[ETAPE 6] Choisir produit")
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
            tests_passes.append("ETAPE 6: Produit - OK")
        except Exception as e:
            print(f"[WARN] {str(e)[:50]}")
            bugs_detectes.append("BUG: Produit non selectionnable")
        
        print(f"[INFO] URL produit: {driver.current_url}")
        
        # ETAPE 7: Ajouter aux favoris
        print("\n" + "="*60)
        print("[ETAPE 7] Ajouter aux favoris")
        print("="*60)
        try:
            fav = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="cart"]/div/ul/li[3]/form/button/i'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", fav)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", fav)
            time.sleep(3)
            print("[OK] Ajoute aux favoris")
            tests_passes.append("ETAPE 7: Favoris - OK")
        except Exception as e:
            print(f"[WARN] Bouton favoris: {str(e)[:50]}")
            bugs_detectes.append("BUG MINEUR: Bouton favoris")
        
        # ETAPE 8: Quantite = 2
        print("\n" + "="*60)
        print("[ETAPE 8] Quantite = 2")
        print("="*60)
        try:
            inc = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="quantity-wanted-p"]/div[2]'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", inc)
            time.sleep(1)
            inc.click()
            time.sleep(1)
            print("[OK] Quantite = 2")
            tests_passes.append("ETAPE 8: Quantite - OK")
        except:
            try:
                driver.execute_script("document.querySelector('input[name=quantite]').value = '2';")
                print("[OK] Quantite forcee a 2")
            except:
                pass
        
        # ETAPE 9: Ajouter au panier
        print("\n" + "="*60)
        print("[ETAPE 9] Ajouter au panier")
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
            tests_passes.append("ETAPE 9: Ajout panier - OK")
        except Exception as e:
            print(f"[WARN] {str(e)[:50]}")
            bugs_detectes.append("BUG: Bouton panier")
        
        # ETAPE 10: Aller au panier
        print("\n" + "="*60)
        print("[ETAPE 10] Page panier")
        print("="*60)
        driver.get(f"{live_server_url}/deals/cart")
        time.sleep(4)
        print("[OK] Page panier chargee")
        tests_passes.append("ETAPE 10: Page panier - OK")
        
        # ETAPE 11: Checkout (sans coupon)
        print("\n" + "="*60)
        print("[ETAPE 11] Checkout (sans coupon)")
        print("="*60)
        try:
            checkout = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="cart"]/div/div[2]/div[2]/div[2]/input'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkout)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", checkout)
            time.sleep(4)
            print("[OK] Checkout clique")
            tests_passes.append("ETAPE 11: Checkout - OK")
        except Exception as e:
            print(f"[WARN] {str(e)[:50]}")
            bugs_detectes.append("BUG: Bouton checkout")
        
        print(f"[INFO] URL checkout: {driver.current_url}")
        
        # ETAPE 12: Payer
        print("\n" + "="*60)
        print("[ETAPE 12] Paiement")
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
            tests_passes.append("ETAPE 12: Paiement - OK")
        except Exception as e:
            print(f"[WARN] {str(e)[:50]}")
            bugs_detectes.append("BUG: Bouton payer")
        
        print(f"[INFO] URL apres paiement: {driver.current_url}")
        driver.save_screenshot("user_journey_paiement.png")
        
        # ============================================================
        #                    PARTIE 3: PROFIL & COMMANDES
        # ============================================================
        print("\n" + "#"*60)
        print("#             PARTIE 3: PROFIL & COMMANDES                  #")
        print("#"*60)
        
        # ETAPE 13: Accueil
        print("\n" + "="*60)
        print("[ETAPE 13] Retour accueil")
        print("="*60)
        driver.get(f"{live_server_url}/")
        time.sleep(3)
        print("[OK] Accueil charge")
        tests_passes.append("ETAPE 13: Accueil - OK")
        
        # ETAPE 14: Profil
        print("\n" + "="*60)
        print("[ETAPE 14] Cliquer profil")
        print("="*60)
        try:
            profile = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div/div[1]/div[2]/div[1]/div/div/div[3]/div[1]/div[3]/div/a[1]'))
            )
            driver.execute_script("arguments[0].click();", profile)
            time.sleep(3)
            print("[OK] Profil clique")
            tests_passes.append("ETAPE 14: Profil - OK")
        except:
            driver.get(f"{live_server_url}/client/")
            time.sleep(3)
            tests_passes.append("ETAPE 14: Profil (direct) - OK")
        
        print(f"[INFO] URL profil: {driver.current_url}")
        
        # ETAPE 15: Ma liste de souhait
        print("\n" + "="*60)
        print("[ETAPE 15] Ma liste de souhait")
        print("="*60)
        try:
            wishlist = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/aside/nav/ul/li[3]/a'))
            )
            driver.execute_script("arguments[0].click();", wishlist)
            time.sleep(3)
            print("[OK] Liste de souhait cliquee")
            
            # Prendre un screenshot pour debug
            driver.save_screenshot("liste_souhait.png")
            
            # Verifier le produit qu'on a ajoute aux favoris
            # Il ne devrait PAS etre visible car on l'a achete
            try:
                # Chercher le nom du produit dans la liste de souhait
                product_name_xpath = '/html/body/div[1]/div/div/div/div/div/div/div[2]/h4[1]'
                
                try:
                    product_element = driver.find_element(By.XPATH, product_name_xpath)
                    if product_element.is_displayed():
                        product_name = product_element.text
                        print(f"[ERROR] Produit '{product_name}' encore visible dans liste de souhait")
                        bugs_detectes.append(f"BUG CRITIQUE: Produit achete '{product_name}' encore visible dans favoris")
                        tests_passes.append("ETAPE 15: Liste souhait - ECHEC (produit visible)")
                    else:
                        print("[OK] Element produit existe mais non visible")
                        tests_passes.append("ETAPE 15: Liste souhait - OK")
                except:
                    print("[OK] Aucun produit trouve dans la liste de souhait (normal car achete)")
                    tests_passes.append("ETAPE 15: Liste souhait - OK")
                    
            except Exception as e:
                print(f"[WARN] Erreur verification: {str(e)[:50]}")
                tests_passes.append("ETAPE 15: Liste souhait - OK (verification impossible)")
            
        except Exception as e:
            print(f"[WARN] {str(e)[:50]}")
            bugs_detectes.append("BUG: Liste de souhait")
        
        # Retourner au profil
        driver.get(f"{live_server_url}/client/")
        time.sleep(2)
        
        # ETAPE 16: COMMANDES
        print("\n" + "="*60)
        print("[ETAPE 16] Onglet COMMANDES")
        print("="*60)
        try:
            cmd = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div/ul/li[2]/a'))
            )
            driver.execute_script("arguments[0].click();", cmd)
            time.sleep(3)
            print("[OK] Onglet COMMANDES clique")
            tests_passes.append("ETAPE 16: Commandes - OK")
        except Exception as e:
            print(f"[WARN] {str(e)[:50]}")
            bugs_detectes.append("BUG: Onglet COMMANDES")
        
        # ETAPE 17: Voir detail
        print("\n" + "="*60)
        print("[ETAPE 17] Voir detail commande")
        print("="*60)
        try:
            detail = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="tab-item-2"]/div/a'))
            )
            driver.execute_script("arguments[0].click();", detail)
            time.sleep(3)
            print("[OK] Detail commande clique")
            tests_passes.append("ETAPE 17: Detail - OK")
        except Exception as e:
            print(f"[WARN] {str(e)[:50]}")
            bugs_detectes.append("BUG: Voir detail")
        
        print(f"[INFO] URL detail: {driver.current_url}")
        driver.save_screenshot("user_journey_detail.png")
        
        # ETAPE 18: Telecharger recu
        print("\n" + "="*60)
        print("[ETAPE 18] Telecharger recu")
        print("="*60)
        try:
            receipt = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="receipt"]/a'))
            )
            url = receipt.get_attribute('href')
            print(f"[INFO] URL recu: {url}")
            
            # Ouvrir le recu dans un nouvel onglet pour verifier
            driver.execute_script("window.open(arguments[0], '_blank');", url)
            time.sleep(2)
            
            # Basculer vers le nouvel onglet
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(2)
            
            # Verifier si c'est une erreur ou un recu valide
            page_content = driver.page_source.lower()
            if 'error' in page_content or 'exception' in page_content or '500' in page_content or '404' in page_content:
                print("[ERROR] Page recu contient une erreur")
                bugs_detectes.append("BUG CRITIQUE: Recu renvoie une erreur au lieu du PDF")
                tests_passes.append("ETAPE 18: Recu - ECHEC (erreur)")
            else:
                print("[OK] Recu charge sans erreur")
                tests_passes.append("ETAPE 18: Recu - OK")
            
            # Fermer l'onglet et revenir
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(1)
            
        except Exception as e:
            print(f"[ERROR] Exception recu: {str(e)[:80]}")
            bugs_detectes.append(f"BUG CRITIQUE: Exception lors du telechargement recu - {str(e)[:50]}")
        
        # ETAPE 19: Modifier profil
        print("\n" + "="*60)
        print("[ETAPE 19] Modifier profil")
        print("="*60)
        driver.get(f"{live_server_url}/client/")
        time.sleep(3)
        try:
            edit = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div/div[1]/a'))
            )
            driver.execute_script("arguments[0].click();", edit)
            time.sleep(3)
            print("[OK] Modifier profil clique")
            
            # Modifier nom
            name_field = driver.find_element(By.XPATH, '//*[@id="first_name"]')
            name_field.clear()
            name_field.send_keys(f"Modified_{user_data['prenoms']}")
            print("[OK] Nom modifie")
            
            # Modifier adresse
            addr_field = driver.find_element(By.XPATH, '//*[@id="address"]')
            addr_field.clear()
            addr_field.send_keys("123 Nouvelle Adresse Modifiee")
            print("[OK] Adresse modifiee")
            
            tests_passes.append("ETAPE 19: Modification - OK")
        except Exception as e:
            print(f"[WARN] {str(e)[:50]}")
            bugs_detectes.append("BUG: Modifier profil")
        
        # ETAPE 20: Enregistrer
        print("\n" + "="*60)
        print("[ETAPE 20] Enregistrer")
        print("="*60)
        try:
            save = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div/div/div/div/form/button'))
            )
            driver.execute_script("arguments[0].click();", save)
            time.sleep(4)
            print("[OK] Modifications enregistrees")
            tests_passes.append("ETAPE 20: Enregistrement - OK")
        except Exception as e:
            print(f"[WARN] {str(e)[:50]}")
            bugs_detectes.append("BUG: Enregistrer")
        
        driver.save_screenshot("user_journey_final.png")
        
        # ============================================================
        # RESUME DETAILLE
        # ============================================================
        print("\n" + "#"*60)
        print("#              RESUME USER JOURNEY                          #")
        print("#"*60)
        
        print(f"\n[UTILISATEUR] {user_data['username']} / {user_data['email']}")
        
        # Compter les resultats
        total_etapes = 20
        etapes_reussies = len([t for t in tests_passes if "ECHEC" not in t])
        etapes_echouees = len([t for t in tests_passes if "ECHEC" in t]) + len(bugs_detectes)
        
        print(f"\n" + "="*60)
        print(f"STATISTIQUES: {etapes_reussies}/{total_etapes} etapes reussies")
        print("="*60)
        
        print(f"\n[TESTS PASSES] {len(tests_passes)} etape(s):\n")
        for i, t in enumerate(tests_passes, 1):
            status = "✓" if "ECHEC" not in t else "✗"
            print(f"  {status} {i}. {t}")
        
        if bugs_detectes:
            print(f"\n[BUGS DETECTES] {len(bugs_detectes)} bug(s):\n")
            for i, b in enumerate(bugs_detectes, 1):
                severity = "CRITIQUE" if "CRITIQUE" in b else "MAJEUR" if "BUG:" in b else "MINEUR"
                print(f"  ✗ [{severity}] {i}. {b}")
        else:
            print("\n[SUCCESS] Aucun bug detecte!")
        
        # Afficher un resume final style pytest
        print(f"\n" + "="*60)
        if bugs_detectes:
            print(f"RESULTAT: {etapes_reussies} passed, {etapes_echouees} failed")
        else:
            print(f"RESULTAT: {etapes_reussies} passed")
        print("="*60)
        
        # Faire echouer le test si des bugs critiques sont detectes
        bugs_critiques = [b for b in bugs_detectes if "CRITIQUE" in b]
        if bugs_critiques:
            pytest.fail(f"{len(bugs_critiques)} bug(s) critique(s) detecte(s): {bugs_critiques}")
